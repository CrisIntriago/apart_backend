from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = "users"

    def __str__(self):
        return self.email
