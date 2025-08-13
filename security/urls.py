from django.urls import path
from knox.views import LogoutView

from .views import (
    LoginView,
    PasswordResetFormView,
    PasswordResetRequestView,
    PasswordResetSuccessView,
    RegisterView,
    ValidateEmailView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("validate-email/", ValidateEmailView.as_view(), name="validate-email"),
    path(
        "password-reset/request/",
        PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "password-reset/<uuid:token>/",
        PasswordResetFormView.as_view(),
        name="password_reset_form",
    ),
    path(
        "password-reset/success/",
        PasswordResetSuccessView.as_view(),
        name="password_reset_success",
    ),
]
