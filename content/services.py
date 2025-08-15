from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.db.models import Count, Max, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from activities.models.base import Activity, UserAnswer
from content.models import Course, Module
from users.models import User
from utils.enums import CONSUME_STATUSES

from .exceptions import NoAttemptsRemainingError
from .models import Exam, ExamAttempt, ExamAttemptStatus


@dataclass(frozen=True)
class CourseProgressResult:
    overall: Dict[str, Any]
    modules: List[Dict[str, Any]]


@dataclass(frozen=True)
class StartAttemptResult:
    attempt: ExamAttempt
    created: bool


class ExamGradingService:
    @staticmethod
    def finalize_and_grade(attempt_id: int) -> ExamAttempt:
        attempt = ExamAttempt.objects.select_related("exam").get(pk=attempt_id)
        exam = attempt.exam

        if attempt.status == ExamAttemptStatus.CANCELLED:
            return attempt
        if attempt.status == ExamAttemptStatus.GRADED:
            return attempt

        exam_activity_qs = exam.activities.all().only("id", "points")
        total_questions = exam_activity_qs.count()
        max_points = (
            exam_activity_qs.aggregate(s=Coalesce(Sum("points"), Value(0)))["s"] or 0
        )

        correct_base = (
            UserAnswer.objects.filter(exam_attempt=attempt, is_correct=True)
            .values("activity_id")
            .distinct()
            .annotate(
                activity_points=Subquery(
                    Activity.objects.filter(pk=OuterRef("activity_id")).values(
                        "points"
                    )[:1]
                )
            )
        )
        score_points = (
            correct_base.aggregate(s=Coalesce(Sum("activity_points"), Value(0)))["s"]
            or 0
        )
        correct_count = correct_base.count()

        percentage = (score_points / max_points * 100) if max_points > 0 else 0.0
        passed = percentage >= exam.pass_mark_percent

        attempt.score_points = score_points
        attempt.max_points = max_points
        attempt.correct_count = correct_count
        attempt.total_questions = total_questions
        attempt.percentage = round(percentage, 2)
        attempt.passed = passed
        attempt.finished_at = attempt.finished_at or timezone.now()
        attempt.graded_at = timezone.now()

        if attempt.status in (
            ExamAttemptStatus.IN_PROGRESS,
            ExamAttemptStatus.SUBMITTED,
        ):
            attempt.status = ExamAttemptStatus.GRADED
        elif attempt.status == ExamAttemptStatus.EXPIRED:
            pass

        attempt.save(
            update_fields=[
                "score_points",
                "max_points",
                "correct_count",
                "total_questions",
                "percentage",
                "passed",
                "finished_at",
                "graded_at",
                "status",
            ]
        )
        return attempt


class CourseProgressService:
    def __init__(self, course: Course, user: User):
        self.course = course
        self.user = user

    def compute(self) -> CourseProgressResult:
        total_activities = Activity.objects.filter(module__course=self.course).count()

        completed_activities = (
            UserAnswer.objects.filter(
                user=self.user,
                activity__module__course=self.course,
                is_correct=True,
            )
            .values("activity_id")
            .distinct()
            .count()
        )

        percent = (
            round((completed_activities * 100 / total_activities), 2)
            if total_activities
            else 0.0
        )

        modules_qs = (
            Module.objects.filter(course=self.course)
            .annotate(
                total=Count("activities", distinct=True),
                completed=Count(
                    "activities",
                    filter=Q(
                        activities__answers__user=self.user,
                        activities__answers__is_correct=True,
                    ),
                    distinct=True,
                ),
            )
            .values("id", "name", "total", "completed")
        )

        modules = []
        for m in modules_qs:
            m_percent = (
                round((m["completed"] * 100 / m["total"]), 2) if m["total"] else 0.0
            )
            modules.append({
                "id": m["id"],
                "name": m["name"],
                "total": m["total"],
                "completed": m["completed"],
                "remaining": max(m["total"] - m["completed"], 0),
                "percent": m_percent,
            })

        return CourseProgressResult(
            overall={
                "total": total_activities,
                "completed": completed_activities,
                "remaining": max(total_activities - completed_activities, 0),
                "percent": percent,
            },
            modules=modules,
        )


class ExamAttemptService:
    @staticmethod
    def lock_exam(exam_id: int) -> Exam:
        return Exam.objects.select_for_update().get(pk=exam_id)

    @staticmethod
    def get_last_attempt_locked(*, exam: Exam, user) -> Optional[ExamAttempt]:
        return (
            ExamAttempt.objects.select_for_update()
            .filter(exam=exam, user=user)
            .order_by("-attempt_number", "-id")
            .first()
        )

    @staticmethod
    def compute_expires_at(
        *, attempt: ExamAttempt, exam: Exam
    ) -> Optional[timezone.datetime]:
        limit = attempt.time_limit_minutes or exam.time_limit_minutes or 0
        if not limit or not attempt.started_at:
            return None
        return attempt.started_at + timedelta(minutes=limit)

    @classmethod
    def mark_expired_if_needed(
        cls, *, attempt: ExamAttempt, exam: Exam, now=None
    ) -> bool:
        if attempt.status != ExamAttemptStatus.IN_PROGRESS:
            return False

        now = now or timezone.now()
        expires_at = cls.compute_expires_at(attempt=attempt, exam=exam)
        if not expires_at or now < expires_at:
            return False

        updated = ExamAttempt.objects.filter(
            pk=attempt.pk, status=ExamAttemptStatus.IN_PROGRESS
        ).update(status=ExamAttemptStatus.EXPIRED, finished_at=expires_at)

        if updated:
            attempt.status = ExamAttemptStatus.EXPIRED
            attempt.finished_at = expires_at
            return True
        return False

    @staticmethod
    def count_used_attempts(*, exam: Exam, user) -> int:
        return ExamAttempt.objects.filter(
            exam=exam,
            user=user,
            status__in=CONSUME_STATUSES,
        ).count()

    @classmethod
    def ensure_attempts_remaining(cls, *, exam: Exam, user) -> None:
        if exam.attempts_allowed:
            used = cls.count_used_attempts(exam=exam, user=user)
            if used >= exam.attempts_allowed:
                raise NoAttemptsRemainingError("No attempts remaining.")

    @staticmethod
    def next_attempt_number(*, exam: Exam, user) -> int:
        last_num = (
            ExamAttempt.objects.filter(exam=exam, user=user)
            .aggregate(m=Max("attempt_number"))
            .get("m")
            or 0
        )
        return last_num + 1

    @staticmethod
    def create_attempt(*, exam: Exam, user, attempt_number: int) -> ExamAttempt:
        return ExamAttempt.objects.create(
            exam=exam,
            user=user,
            attempt_number=attempt_number,
            time_limit_minutes=exam.time_limit_minutes,
            status=ExamAttemptStatus.IN_PROGRESS,
            started_at=timezone.now(),
        )

    @classmethod
    @transaction.atomic
    def start_attempt(cls, *, exam_id: int, user) -> StartAttemptResult:
        exam = cls.lock_exam(exam_id)
        last = cls.get_last_attempt_locked(exam=exam, user=user)

        if last and last.status == ExamAttemptStatus.IN_PROGRESS:
            expired_now = cls.mark_expired_if_needed(attempt=last, exam=exam)
            if not expired_now:
                return StartAttemptResult(attempt=last, created=False)

        cls.ensure_attempts_remaining(exam=exam, user=user)

        num = cls.next_attempt_number(exam=exam, user=user)
        attempt = cls.create_attempt(exam=exam, user=user, attempt_number=num)
        return StartAttemptResult(attempt=attempt, created=True)
