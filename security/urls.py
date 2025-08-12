from django.urls import path
from knox.views import LogoutView

from .views import LoginView, RegisterView, ValidateEmailView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("validate-email/", ValidateEmailView.as_view(), name="validate-email"),
]
