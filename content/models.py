from django.db import models

from languages.models import Language
from people.models import Student
from utils.enums import DifficultyLevel


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
