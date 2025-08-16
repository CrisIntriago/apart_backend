from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from languages.models import Language
from users.models import User
from utils.enums import EnrollmentStatus, ProficiencyLevel


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
    first_name = models.CharField(max_length=100, default="")
    last_name = models.CharField(max_length=100, default="")
    date_of_birth = models.DateField(default=None)
    photo = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL o ruta de la foto de perfil."
    )
    country = models.CharField(max_length=100, default="")
    languages = models.JSONField(default=list)
    has_access = models.BooleanField(default=False)

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

    active_course = models.ForeignKey(
        "content.Course",
        on_delete=models.SET_NULL,
        related_name="active_students",
        null=True,
        blank=True,
        help_text="Curso actualmente activo del estudiante.",
    )

    description = models.TextField(
        null=True, blank=True, help_text="Descripción breve sobre el estudiante."
    )

    def __str__(self):
        return f"{self.person.first_name} {self.person.last_name} (Student)"

    def clean(self):
        super().clean()
        if self.active_course_id:
            now = timezone.now()
            has_active_enrollment = (
                self.enrollments.filter(
                    course_id=self.active_course_id,
                    status=EnrollmentStatus.ACTIVE,
                )
                .filter(
                    models.Q(start_at__isnull=True) | models.Q(start_at__lte=now),
                    models.Q(end_at__isnull=True) | models.Q(end_at__gte=now),
                )
                .exists()
            )
            if not has_active_enrollment:
                raise ValidationError({
                    "active_course": "El curso seleccionado no está activo para este estudiante en este momento."  # noqa: E501
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def set_active_course(self, course):
        self.active_course = course
        self.full_clean()
        self.save(update_fields=["active_course"])


class Enrollment(models.Model):
    class Meta:
        db_table = "enrollments"
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"], name="uq_enrollment_student_course"
            ),
            models.UniqueConstraint(
                fields=["student"],
                condition=models.Q(status=EnrollmentStatus.ACTIVE),
                name="uq_one_active_enrollment_per_student",
            ),
        ]
        indexes = [
            models.Index(fields=["student", "course", "status"]),
        ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(
        "content.Course", on_delete=models.CASCADE, related_name="enrollments"
    )

    status = models.CharField(
        max_length=12, choices=EnrollmentStatus.choices, default=EnrollmentStatus.ACTIVE
    )
    enrolled_at = models.DateTimeField(default=timezone.now)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    role = models.CharField(max_length=20, blank=True, default="student")
    notes = models.TextField(blank=True, default="")

    progress_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, blank=True
    )
    last_activity_at = models.DateTimeField(null=True, blank=True)

    def is_active_now(self):
        now = timezone.now()
        if self.status != EnrollmentStatus.ACTIVE:
            return False
        if self.start_at and now < self.start_at:
            return False
        if self.end_at and now > self.end_at:
            return False
        return True

    def __str__(self):
        return f"{self.student} enrolled in {self.course} ({self.status})"


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
