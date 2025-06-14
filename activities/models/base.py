from django.db import models

from users.models import User


class DificultyLevel(models.TextChoices):
    EASY = "easy", "Fácil"
    MEDIUM = "medium", "Medio"
    HARD = "hard", "Difícil"


class BaseActivity(models.Model):
    title = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    difficulty = models.CharField(
        max_length=20,
        choices=DificultyLevel.choices,
        default=DificultyLevel.MEDIUM,
        help_text="Nivel de dificultad de la actividad",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class UserAnswer(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    activity_type = models.CharField(max_length=50)
    activity_id = models.PositiveIntegerField()
    response_data = models.JSONField()
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_answer"
