# exams/services.py
from django.db.models import OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from activities.models.base import Activity, UserAnswer

from .models import ExamAttempt, ExamAttemptStatus


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
