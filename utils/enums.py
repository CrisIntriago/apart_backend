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

    # TODO: Implement requirements asked by client

    # MULTIPLE_OPTION_THEORY = 'MULTIPLE_OPTION_THEORY',         // FR 19
    # MULTIPLE_OPTION_INCOMPLETE_SENTENCE = 'MULTIPLE_OPTION_INCOMPLETE_SENTENCE', // FR 20  # noqa: E501
    # MULTIPLE_OPTION_VOCABULARY = 'MULTIPLE_OPTION_VOCABULARY', // FR 21
    # MULTIPLE_OPTION_IMAGE = 'MULTIPLE_OPTION_IMAGE',           // FR 22
    # WRITTEN_RESPONSE = 'WRITTEN_RESPONSE',                     // FR 23
    # SHOW_RESULTS = 'SHOW_RESULTS',                             // FR 25


class ProficiencyLevel(models.TextChoices):
    BEGINNER = "A1", "Beginner (A1)"
    ELEMENTARY = "A2", "Elementary (A2)"
    INTERMEDIATE = "B1", "Intermediate (B1)"
    UPPER_INTERMEDIATE = "B2", "Upper Intermediate (B2)"
    ADVANCED = "C1", "Advanced (C1)"
    PROFICIENT = "C2", "Proficient (C2)"
    NATIVE = "N", "Native"


class ExamType(models.TextChoices):
    MIDTERM = "MIDTERM", "Parcial"
    FINAL = "FINAL", "Final"


class ExamAttemptStatus(models.TextChoices):
    IN_PROGRESS = "in_progress", "In progress"
    SUBMITTED = "submitted", "Submitted"
    GRADED = "graded", "Graded"
    CANCELLED = "cancelled", "Cancelled"
    EXPIRED = "expired", "Expired"
