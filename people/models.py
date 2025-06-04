from django.db import models
from users.models import User


class Person(models.Model):
    class Meta:
        verbose_name = 'Person'
        verbose_name_plural = 'People'
        db_table = 'people'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='person',
        null=True,
        blank=True,
    )
    national_id = models.CharField(max_length=10, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Student(models.Model):
    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        db_table = 'students'

    person = models.OneToOneField(
        Person,
        on_delete=models.CASCADE,
        related_name='student',
        null=True,
        blank=True,
    )
    progress = models.IntegerField(default=0)
    vocabulary = models.TextField(null=True, blank=True)
    subscription = models.CharField(max_length=50, null=True, blank=True)
