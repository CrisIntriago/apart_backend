# exams/services.py
from dataclasses import dataclass
from typing import Any, Dict, List

from django.db.models import Count, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from activities.models.base import Activity, UserAnswer
from content.models import Course, Module
from users.models import User

from .models import ExamAttempt, ExamAttemptStatus


@dataclass(frozen=True)
class CourseProgressResult:
    overall: Dict[str, Any]
    modules: List[Dict[str, Any]]


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
    """
    Calcula el avance de un curso para un usuario:
    - overall: totales del curso (total, completadas, restantes, porcentaje)
    - modules: lista de módulos con su propio avance
    """

    def __init__(self, course: Course, user: User):
        self.course = course
        self.user = user

    def compute(self) -> CourseProgressResult:
        total_activities = Activity.objects.filter(module__course=self.course).count()

        completed_activities = (
            UserAnswer.objects.filter(
                user=self.user,
                activity__module__course=self.course,
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
                    filter=Q(activities__answers__user=self.user),
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
