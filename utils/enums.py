from django.db import models


class DifficultyLevel(models.TextChoices):
    EASY = "easy", "Fácil"
    MEDIUM = "medium", "Medio"
    HARD = "hard", "Difícil"


class ActivityType(models.TextChoices):
    CHOICE = "choice", "Opción múltiple"
    FILL = "fill_in", "Completar"
    MATCH = "matching", "Unir"
    ORDER = "order", "Ordenar"
