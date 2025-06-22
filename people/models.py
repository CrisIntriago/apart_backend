from django.db import models

from languages.models import Language
from users.models import User
from utils.enums import ProficiencyLevel


class Person(models.Model):
    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "People"
        db_table = "people"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="person",
        null=True,
        blank=True,
    )
    national_id = models.CharField(max_length=10, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    photo = models.ImageField(
        upload_to="people/photos/",
        null=True,
        blank=True,
    )
    country = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Student(models.Model):
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
        db_table = "students"

    person = models.OneToOneField(
        Person,
        on_delete=models.CASCADE,
        related_name="student",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.person.first_name} {self.person.last_name} (Student)"


class StudentLanguageProficiency(models.Model):
    class Meta:
        unique_together = ("student", "language")
        verbose_name = "Student Language Proficiency"
        verbose_name_plural = "Student Language Proficiencies"
        db_table = "student_language_proficiencies"

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="language_proficiencies"
    )
    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, related_name="student_proficiencies"
    )
    level = models.CharField(
        max_length=2,
        choices=ProficiencyLevel.choices,
        default=ProficiencyLevel.BEGINNER,
    )

    def __str__(self):
        return f"{self.student} - {self.language} ({self.get_level_display()})"
