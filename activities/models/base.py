from django.db import models

from users.models import User
from utils.enums import ActivityType, DifficultyLevel


class Activity(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "activity"
        abstract = False


class UserAnswer(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="answers",
        blank=True,
        null=True,
    )
    activity_type = models.CharField(max_length=50)
    activity_id = models.PositiveIntegerField()
    response_data = models.JSONField()
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_answer"
