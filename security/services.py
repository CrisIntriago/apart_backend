from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, Protocol

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from knox.models import AuthToken

from people.models import Person
from users.models import User, UserToken

from .exceptions import PasswordValidationError, TokenExpired, TokenInvalid

DEFAULT_EXPIRY_HOURS = getattr(settings, "PASSWORD_RESET_EXPIRY_HOURS", 48)
FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", None)


def register_user(validated_data):
    user = User.objects.create_user(
        username=validated_data["username"],
        email=validated_data.get("email"),
        phone=validated_data.get("phone"),
        password=validated_data["password"],
    )

    Person.objects.create(
        user=user,
        first_name=validated_data["first_name"],
        last_name=validated_data["last_name"],
        date_of_birth=validated_data["date_of_birth"],
        country=validated_data["country"],
        languages=validated_data["languages"],
        photo=validated_data["photo"] if "photo" in validated_data else None,
    )
    return user


def register_token(user):
    return AuthToken.objects.create(user)[1]


def login_user(user):
    return AuthToken.objects.create(user)[1]


class EmailPort(Protocol):
    def send_password_reset(self, to_email: str, reset_url: str) -> None: ...


class DjangoEmailAdapter:
    subject = "Password reset"

    def __init__(
        self,
        from_email: Optional[str] = FROM_EMAIL,
        expiry_hours: int = DEFAULT_EXPIRY_HOURS,
        brand_name: str = "Apart",
        brand_color: str = "#111827",
    ):
        self.from_email = from_email
        self.expiry_hours = expiry_hours
        self.brand_name = brand_name
        self.brand_color = brand_color

    def send_password_reset(self, to_email: str, reset_url: str) -> None:
        context = {
            "reset_url": reset_url,
            "expiry_hours": self.expiry_hours,
            "brand_name": self.brand_name,
            "brand_color": self.brand_color,
        }

        html_body = render_to_string("emails/password_reset.html", context)
        text_body = render_to_string("emails/password_reset.txt", context)

        msg = EmailMultiAlternatives(
            subject=self.subject,
            body=text_body or "",
            from_email=self.from_email,
            to=[to_email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)


@dataclass(frozen=True)
class TokenCheck:
    is_valid: bool
    reason: Optional[str] = None


class TokenService:
    def __init__(self, expiry_hours: int = DEFAULT_EXPIRY_HOURS):
        self.expiry_hours = expiry_hours

    def issue_recovery(self, user: User) -> UserToken:
        return UserToken.objects.create(user=user, type=UserToken.Type.RECOVERY)

    def _get_token(self, token: uuid.UUID) -> Optional[UserToken]:
        try:
            return UserToken.objects.select_related("user").get(
                token=token, type=UserToken.Type.RECOVERY
            )
        except UserToken.DoesNotExist:
            return None

    def check(self, token: uuid.UUID) -> TokenCheck:
        token_obj = self._get_token(token)
        if token_obj is None:
            return TokenCheck(False, "not_found")
        if token_obj.used:
            return TokenCheck(False, "used")
        expires_at = token_obj.created_at + timedelta(hours=self.expiry_hours)
        if timezone.now() > expires_at:
            return TokenCheck(False, "expired")
        return TokenCheck(True)

    def get_valid_token_or_raise(self, token: uuid.UUID) -> UserToken:
        token_obj = self._get_token(token)
        if token_obj is None:
            raise TokenInvalid("Token not found.")
        if token_obj.used:
            raise TokenExpired("Token already used.")
        expires_at = token_obj.created_at + timedelta(hours=self.expiry_hours)
        if timezone.now() > expires_at:
            raise TokenExpired("Token expired.")
        return token_obj

    def mark_used(self, token_obj: UserToken) -> None:
        token_obj.used = True
        token_obj.save(update_fields=["used"])


class PasswordService:
    def validate(self, user: User, raw_password: str) -> None:
        try:
            validate_password(raw_password, user=user)
        except ValidationError as e:
            raise PasswordValidationError(e.messages)

    def set(self, user: User, raw_password: str) -> None:
        user.set_password(raw_password)
        user.save(update_fields=["password"])


class PasswordResetService:
    def __init__(
        self,
        token_svc: Optional[TokenService] = None,
        pwd_svc: Optional[PasswordService] = None,
        email_port: Optional[EmailPort] = None,
    ):
        self.tokens = token_svc or TokenService()
        self.passwords = pwd_svc or PasswordService()
        self.email = email_port or DjangoEmailAdapter()

    def request_reset(
        self, email: str, request=None, absolute_base_url: Optional[str] = None
    ) -> None:
        email_norm = (email or "").strip().lower()
        try:
            user = User.objects.get(email=email_norm)
        except User.DoesNotExist:
            return

        token_obj = self.tokens.issue_recovery(user)
        reset_url = self._build_reset_url(token_obj.token, request, absolute_base_url)
        self.email.send_password_reset(to_email=email_norm, reset_url=reset_url)

    def _build_reset_url(
        self, token: uuid.UUID, request=None, absolute_base_url: Optional[str] = None
    ) -> str:
        path = reverse("password_reset_form", kwargs={"token": str(token)})
        if request is not None:
            return request.build_absolute_uri(path)
        if absolute_base_url:
            return absolute_base_url.rstrip("/") + path
        return path

    def check_token(self, token: uuid.UUID) -> TokenCheck:
        return self.tokens.check(token)

    def reset_with_token(self, token: uuid.UUID, new_password: str) -> None:
        token_obj = self.tokens.get_valid_token_or_raise(token)
        self.passwords.validate(token_obj.user, new_password)
        self.passwords.set(token_obj.user, new_password)
        self.tokens.mark_used(token_obj)
