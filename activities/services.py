from datetime import timedelta
from typing import Any, Dict, Iterable, List, Optional

from django.db import transaction
from django.db.models import Count, F, QuerySet, Sum, Window
from django.db.models.functions import Rank
from django.shortcuts import get_object_or_404
from django.utils import timezone

from activities.models.base import Activity, UserAnswer
from activities.models.matching import MatchingActivity
from activities.strategies.validation.registry import ValidationStrategyRegistry
from content.models import Course, Vocabulary
from people.models import Enrollment, EnrollmentStatus, Person, Student
from utils.enums import ActivityType

from .services import CourseProgressService


class AnswerSubmissionService:
    def __init__(self, user, activity_id, input_data, exam_attempt=None):
        self.user = user
        self.activity_id = activity_id
        self.input_data = input_data
        self.exam_attempt = exam_attempt

    def execute(self):
        activity = self._get_activity()
        serializer = self._get_validated_serializer(activity)
        is_correct = self._validate_response(activity, serializer.validated_data)
        user_answer = self._save_user_answer(
            activity, serializer.validated_data, is_correct
        )
        transaction.on_commit(lambda: self._create_vocabulary_if_applicable(activity))
        transaction.on_commit(
            lambda: self._update_enrollment_progress(activity.module.course)
        )
        return user_answer

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
            activity=activity,
            response_data=response_data,
            is_correct=is_correct,
            exam_attempt=self.exam_attempt,
        )

    def _create_vocabulary_if_applicable(self, activity: Activity):
        difficulty = activity.difficulty
        if activity.type != ActivityType.MATCH:
            return
        try:
            activity = MatchingActivity.objects.get(pk=activity.id)
        except MatchingActivity.DoesNotExist:
            return
        try:
            student_id = (
                Student.objects.select_related("person")
                .only("id", "person__id")
                .values_list("id", flat=True)
                .get(person__user_id=self.user.id)
            )
        except Student.DoesNotExist:
            return

        pairs_qs = activity.pairs.filter(is_vocabulary=True).values("left", "right")
        if not pairs_qs:
            return

        vocab_to_create = [
            Vocabulary(
                student_id=student_id,
                word=row["left"],
                meaning=row["right"],
                difficulty=difficulty,
            )
            for row in pairs_qs
        ]

        if not vocab_to_create:
            return

        with transaction.atomic():
            Vocabulary.objects.bulk_create(vocab_to_create, ignore_conflicts=True)

    @classmethod
    @transaction.atomic
    def submit_many(cls, user, answers_payload, exam_attempt=None):
        created = []
        for item in answers_payload:
            svc = cls(
                user=user,
                activity_id=item["activity_id"],
                input_data=item["input_data"],
                exam_attempt=exam_attempt,
            )
            created.append(svc.execute())
        return created

    def _update_enrollment_progress(self, course: Course):
        enrollment = Enrollment.objects.filter(
            student__person__user=self.user,
            course=course,
            status=EnrollmentStatus.ACTIVE,
        ).first()

        if not enrollment:
            return

        progress_service = CourseProgressService(course=course, user=self.user)
        progress_data = progress_service.compute()

        enrollment.progress_percent = progress_data.overall["percent"]
        enrollment.save(update_fields=["progress_percent"])


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
