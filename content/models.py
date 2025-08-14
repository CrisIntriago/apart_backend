from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from languages.models import Language
from people.models import Student
from users.models import User
from utils.enums import DifficultyLevel, ExamAttemptStatus, ExamType


class Course(models.Model):
    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        db_table = "courses"

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="courses/images/", blank=True, null=True)
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="courses",
        blank=True,
        null=True,
    )
    difficulty = models.CharField(
        max_length=50,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
        blank=True,
    )
    students = models.ManyToManyField(
        "people.Student",
        through="people.Enrollment",
        related_name="courses",
        blank=True,
    )

    def __str__(self):
        return f"{self.name}"


class Module(models.Model):
    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        db_table = "modules"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="modules/images/", blank=True, null=True)
    difficulty = models.CharField(
        max_length=50,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
        blank=True,
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora en que finaliza el módulo",
    )

    def __str__(self):
        return f"{self.course.name} - {self.name}"


class Vocabulary(models.Model):
    class Meta:
        verbose_name = "Vocabulary"
        verbose_name_plural = "Vocabularies"
        db_table = "vocabulary"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "word"], name="uq_vocab_student_word"
            )
        ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="vocabularies"
    )
    word = models.CharField(max_length=100)
    meaning = models.TextField()
    difficulty = models.CharField(
        max_length=50,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
        blank=True,
    )

    def __str__(self):
        return f"{self.word} - {self.student}"


class Exam(models.Model):
    class Meta:
        db_table = "exam"
        verbose_name = "Exam"
        verbose_name_plural = "Exams"
        constraints = [
            models.UniqueConstraint(
                fields=["course", "type"], name="uniq_exam_per_course_and_type"
            )
        ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="exams")
    type = models.CharField(max_length=20, choices=ExamType.choices)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    attempts_allowed = models.PositiveIntegerField(default=1)
    pass_mark_percent = models.PositiveSmallIntegerField(
        default=60, help_text="Porcentaje mínimo para aprobar (0-100)"
    )
    activities = models.ManyToManyField(
        "activities.Activity",
        through="activities.ExamActivity",
        related_name="in_exams",
        blank=True,
    )

    def __str__(self):
        return f"{self.course.name} - {self.get_type_display()}" + (
            f" ({self.title})" if self.title else ""
        )


class ExamAttempt(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="exam_attempts"
    )
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ExamAttemptStatus.choices,
        default=ExamAttemptStatus.IN_PROGRESS,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    attempt_number = models.PositiveIntegerField(default=1)

    score_points = models.PositiveIntegerField(default=0)
    max_points = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    passed = models.BooleanField(default=False)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "exam_attempt"
        indexes = [models.Index(fields=["exam", "user", "status"])]
        constraints = [
            models.UniqueConstraint(
                fields=["exam", "user", "attempt_number"],
                name="uniq_attempt_per_exam_user_number",
            )
        ]

    def expires_at(self):
        if self.time_limit_minutes:
            return self.started_at + timezone.timedelta(minutes=self.time_limit_minutes)
        return None

    def is_expired(self):
        exp = self.expires_at()
        return bool(exp and timezone.now() > exp)
