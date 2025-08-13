from django.db import models

from content.models import Exam, Module
from users.models import User
from utils.enums import ActivityType, DifficultyLevel


class Activity(models.Model):
    class Meta:
        db_table = "activity"
        abstract = False

    title = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    difficulty = models.CharField(
        max_length=20,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
        help_text="Nivel de dificultad de la actividad",
    )
    type = models.CharField(
        max_length=20,
        choices=ActivityType.choices,
        default=ActivityType.CHOICE,
        help_text="Tipo de actividad",
    )
    points = models.PositiveIntegerField(
        default=0, help_text="Cantidad de puntos que otorga la actividad"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="activities",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.title} ({self.get_type_display()}) - {self.get_difficulty_display()}"  # noqa: E501


class ExamActivity(models.Model):
    class Meta:
        db_table = "exam_activity"
        unique_together = ("exam", "activity")
        ordering = ("position", "id")

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="exam_items")
    activity = models.ForeignKey(
        "activities.Activity", on_delete=models.CASCADE, related_name="exam_items"
    )
    required = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Examen: {self.exam.title} - Actividad: {self.activity.title}"


class UserAnswer(models.Model):
    class Meta:
        db_table = "user_answer"
        indexes = [
            models.Index(fields=["user", "activity", "is_correct"]),
            models.Index(fields=["exam_attempt", "activity"]),
        ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="answers", blank=True, null=True
    )
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="answers",
        null=True,
        blank=True,
    )
    exam_attempt = models.ForeignKey(
        "content.ExamAttempt",
        on_delete=models.CASCADE,
        related_name="answers",
        null=True,
        blank=True,
        help_text="Si la respuesta pertenece a un examen, referencia el intento.",
    )
    response_data = models.JSONField()
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)
