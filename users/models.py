from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = "users"

    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True)  

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"] 

    def __str__(self):
        return self.email
