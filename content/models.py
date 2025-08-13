from django.db import models

from languages.models import Language
from people.models import Student
from utils.enums import DifficultyLevel, ExamType


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

    def __str__(self):
        return f"{self.course.name} - {self.name}"


class Vocabulary(models.Model):
    class Meta:
        verbose_name = "Vocabulary"
        verbose_name_plural = "Vocabularies"
        db_table = "vocabulary"

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="vocabularies"
    )
    word = models.CharField(max_length=100)
    meaning = models.TextField()

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
