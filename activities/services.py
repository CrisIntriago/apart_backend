from datetime import timedelta
from typing import Any, Dict, Iterable, List, Optional

from django.db.models import Count, F, QuerySet, Sum, Window
from django.db.models.functions import Rank
from django.shortcuts import get_object_or_404
from django.utils import timezone

from activities.models.base import Activity, UserAnswer
from activities.strategies.validation.registry import ValidationStrategyRegistry
from people.models import Person


class AnswerSubmissionService:
    def __init__(self, user, activity_id, input_data):
        self.user = user
        self.activity_id = activity_id
        self.input_data = input_data

    def execute(self):
        activity = self._get_activity()
        serializer = self._get_validated_serializer(activity)
        is_correct = self._validate_response(activity, serializer.validated_data)
        return self._save_user_answer(activity, serializer.validated_data, is_correct)

    def _get_activity(self):
        return get_object_or_404(Activity, pk=self.activity_id)

    def _get_validated_serializer(self, activity):
        serializer_class = ValidationStrategyRegistry.get_serializer(activity.type)
        if serializer_class is None:
            raise ValueError(f"No serializer para tipo '{activity.type}'")
        serializer = serializer_class(data=self.input_data)
        serializer.is_valid(raise_exception=True)
        self.validated_data = serializer.validated_data
        return serializer

    def _validate_response(self, activity, validated_data):
        strategy = ValidationStrategyRegistry.get_strategy(activity.type)
        if strategy is None:
            raise ValueError(f"No estrategia para tipo '{activity.type}'")
        return strategy.validate(activity, validated_data)

    def _save_user_answer(self, activity, response_data, is_correct):
        return UserAnswer.objects.create(
            user=self.user,
            activity_type=activity.type,
            activity=activity,
            response_data=response_data,
            is_correct=is_correct,
        )


class LeaderboardService:
    def __init__(
        self,
        request_user_id: Optional[int],
        limit: int = 10,
        time_window: str = "all",
        module_id: Optional[int] = None,
    ):
        self.request_user_id = request_user_id
        self.limit = limit
        self.time_window = time_window
        self.module_id = module_id

    def execute(self) -> List[Dict[str, Any]]:
        pairs_qs = self._pairs_correctos_unicos()
        leaderboard_qs = self._leaderboard_qs(pairs_qs)
        rows = self._top_n_mas_usuario(leaderboard_qs)
        return self._armar_payload(rows)

    def _since_dt(self):
        now = timezone.now()
        return {
            "day": now - timedelta(days=1),
            "week": now - timedelta(weeks=1),
            "month": now - timedelta(days=30),
            "all": None,
        }.get(self.time_window, None)

    def _base_answers(self) -> QuerySet:
        qs = UserAnswer.objects.filter(is_correct=True).select_related("activity")
        since = self._since_dt()
        if since:
            qs = qs.filter(answered_at__gte=since)
        if self.module_id:
            qs = qs.filter(activity__module_id=self.module_id)
        return qs

    def _pairs_correctos_unicos(self) -> QuerySet:
        return (
            self._base_answers()
            .values("user_id", "activity_id")
            .distinct()
            .annotate(points=F("activity__points"))
        )

    def _leaderboard_qs(self, pairs_qs: QuerySet) -> QuerySet:
        return (
            pairs_qs.values("user_id")
            .annotate(
                total_points=Sum("points"),
                activities_count=Count("activity_id"),
            )
            .annotate(
                position=Window(
                    expression=Rank(),
                    order_by=(F("total_points").desc(), F("user_id").asc()),
                )
            )
            .order_by(F("total_points").desc(), F("user_id").asc())
        )

    def _top_n_mas_usuario(self, qs: QuerySet) -> List[Dict[str, Any]]:
        topn = list(qs[: self.limit])
        if not self.request_user_id:
            return topn
        if any(r["user_id"] == self.request_user_id for r in topn):
            return topn
        extra = qs.filter(user_id=self.request_user_id).first()
        if extra:
            topn.append(extra)
        return topn

    def _person_map(self, user_ids: Iterable[int]) -> Dict[int, Person]:
        persons = (
            Person.objects.filter(user_id__in=list(user_ids))
            .select_related("user")
            .only("user__id", "user__username", "first_name", "last_name")
        )
        return {p.user_id: p for p in persons}

    def _armar_payload(self, rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        user_ids = [r["user_id"] for r in rows]
        pmap = self._person_map(user_ids)
        out: List[Dict[str, Any]] = []
        for r in rows:
            p = pmap.get(r["user_id"])
            username = p.user.username if p and p.user_id else ""
            full_name = f"{p.first_name} {p.last_name}".strip() if p else ""
            out.append({
                "user_id": r["user_id"],
                "username": username,
                "full_name": full_name,
                "total_points": r.get("total_points") or 0,
                "activities_count": r.get("activities_count") or 0,
                "position": r.get("position"),
            })
        return out
