import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = "users"

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)


    def __str__(self):
        return self.email

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]


class UserToken(models.Model):
    class Type(models.TextChoices):
        ACTIVATION = "activate", "Account Activation"
        RECOVERY = "recover", "Password Recovery"
        VERIFICATION = "verify", "Email Verification"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    type = models.CharField(
        max_length=20, choices=Type.choices, default=Type.ACTIVATION
    )
    token = models.UUIDField(
        primary_key=True, default=uuid.uuid4, unique=True, editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        db_table = "user_token"
