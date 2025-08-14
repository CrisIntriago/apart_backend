import uuid
import requests

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate

from content.serializers import CourseSerializer
from users.models import User
from .exceptions import (
    PasswordValidationError,
    TokenExpired,
    TokenInvalid,
)
from .serializers import (
    EmailValidationSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    RegisterGoogleSerializer,
    LoginGoogleSerializer,
)
from .services import PasswordResetService, login_user, register_token, register_user
import logging


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request={
            "application/json": RegisterSerializer,
            "application/json;google": RegisterGoogleSerializer,
        },
        responses={201: None},
        summary="Registro de usuario",
        description="Registra un nuevo usuario y devuelve su token (puede autenticarse usando google o email)",
    )
    def post(self, request):
        google_token = request.data.get("google_token")
        if google_token:
            try:
                url = f"https://oauth2.googleapis.com/tokeninfo?id_token={google_token}"
                response = requests.get(url)
                google_data = response.json()

                if response.status_code != 200 or "email" not in google_data:
                    return Response({"detail": ("Token de Google no válido.")}, status=status.HTTP_400_BAD_REQUEST)
                return Response(
                    {
                        "user": {
                            "email": google_data["email"],
                            "username": google_data["name"],
                            # TO-DO: Guardar la imagen
                            "password": User.make_random_password(),
                        },
                        "token": "notokenyet",
                    },
                    status=status.HTTP_201_CREATED,
                )
            except requests.exceptions.RequestException:
                return Response({"detail": "Error al verificar el token de Google."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = register_user(serializer.validated_data)
        token = register_token(user)
        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.person.first_name,
                    "last_name": user.person.last_name,
                    "country": user.person.country,
                    "date_of_birth": user.person.date_of_birth,
                    "languages": user.person.languages,
                },
                "token": token,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
         request={
            "application/json": LoginSerializer,
            "application/json;google": LoginGoogleSerializer,
        },
        responses={200: None},
        summary="Inicio de sesión",
        description="Inicia sesión con un usuario y devuelve su token",
        auth=[],
    )
    def post(self, request):
        google_token = request.data.get("google_token")
        if google_token:
            try:
                url = f"https://oauth2.googleapis.com/tokeninfo?id_token={google_token}"
                response = requests.get(url)
                google_data = response.json()

                if response.status_code != 200 or "email" not in google_data:
                    return Response({"detail": ("Token de Google no válido.")}, status=status.HTTP_400_BAD_REQUEST)

                email = google_data["email"]
                user_model = get_user_model()
                try:
                    user = user_model.objects.get(email=email)
                except user_model.DoesNotExist:
                    return Response(
                        {
                            "user": {
                                "username": google_data.get("name", ""),
                                "email": google_data["email"],
                                "password": User.make_random_password(),
                            }
                        },
                        status=status.HTTP_404_NOT_FOUND
                    )

                login(request, user,
                      backend='django.contrib.auth.backends.ModelBackend')
                user = user_model.objects.get(email=email)
                print(f"Usuario autenticado: {user}")
                token = login_user(user)
                courses_data = []
                person = getattr(user, "person", None)
                print(f"Person: {person}")
                student = getattr(person, "student", None) if person else None
                if student and getattr(student, "course", None):
                    courses_data = CourseSerializer(
                        [student.course], many=True).data
                return Response(
                    {
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "phone": user.phone,
                            "first_name": user.person.first_name,
                            "last_name": user.person.last_name,
                            "country": user.person.country,
                            "date_of_birth": user.person.date_of_birth,
                            "languages": user.person.languages,
                            "courses": courses_data,
                        },
                        "token": token,
                    },
                    status=status.HTTP_200_OK,
                )
            except requests.exceptions.RequestException:
                return Response({"detail": ("Error al verificar el token de Google.")}, status=status.HTTP_400_BAD_REQUEST)

        # Login tradicional
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        token = login_user(user)
        courses_data = []
        person = getattr(user, "person", None)
        student = getattr(person, "student", None) if person else None
        if student and getattr(student, "course", None):
            courses_data = CourseSerializer([student.course], many=True).data

        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone,
                    "first_name": user.person.first_name,
                    "last_name": user.person.last_name,
                    "country": user.person.country,
                    "date_of_birth": user.person.date_of_birth,
                    "languages": user.person.languages,
                    "courses": courses_data,
                },
                "token": token,
            },
            status=status.HTTP_200_OK,
        )


class ValidateEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=EmailValidationSerializer,
        responses={200: {"description": "Indica si el email existe o no"}},
        summary="Validar email",
        description="Verifica si un correo electrónico ya está registrado en el sistema.",  # noqa: E501
        auth=[],
    )
    def post(self, request):
        serializer = EmailValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        exists = User.objects.filter(email__iexact=email).exists()
        return Response({"exists": exists}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Solicitar enlace para restablecer contraseña",
        description=(
            "Recibe un correo electrónico y, si existe un usuario registrado con ese correo, "  # noqa: E501
            "envía un enlace para restablecer la contraseña válido por **48 horas**. "
            "Por seguridad, este endpoint siempre devuelve **200 OK** y no revela "
            "si el correo está registrado o no."
        ),
        request=PasswordResetRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description=(
                    "Mensaje de confirmación. "
                    "La respuesta es la misma tanto si el correo existe como si no."
                ),
                examples=[
                    OpenApiExample(
                        "Éxito (el correo puede existir o no)",
                        value={
                            "detail": "Si el correo existe, se ha enviado un enlace para restablecer la contraseña."  # noqa: E501
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Error de validación (por ejemplo, formato de correo no válido).",  # noqa: E501
                examples=[
                    OpenApiExample(
                        "Formato de correo inválido",
                        value={
                            "email": [
                                "Introduzca una dirección de correo electrónico válida."
                            ]
                        },
                    )
                ],
            ),
        },
        examples=[
            OpenApiExample(
                name="Ejemplo de solicitud",
                value={"email": "usuario@ejemplo.com"},
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        ser = PasswordResetRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        PasswordResetService().request_reset(
            email=ser.validated_data["email"],
            request=request,
        )
        return Response(
            {"detail": "If the email exists, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetFormView(View):
    template_name = "password_reset_form.html"

    def get(self, request, token):
        svc = PasswordResetService()
        check = svc.check_token(self._parse(token))
        if not check.is_valid:
            return render(
                request, self.template_name, {
                    "invalid": True, "reason": check.reason}
            )
        return render(request, self.template_name, {"token": token})

    def post(self, request, token):
        svc = PasswordResetService()
        try:
            svc.reset_with_token(self._parse(
                token), request.POST.get("password", ""))
        except TokenInvalid:
            return render(
                request, self.template_name, {
                    "invalid": True, "reason": "not_found"}
            )
        except TokenExpired:
            return render(
                request, self.template_name, {
                    "invalid": True, "reason": "expired"}
            )
        except PasswordValidationError as e:
            messages.error(request, "; ".join(e.messages))
            return render(request, self.template_name, {"token": token})

        messages.success(request, "Your password has been reset successfully.")
        return redirect("password_reset_success")

    def _parse(self, token: str) -> uuid.UUID:
        return uuid.UUID(str(token))


class PasswordResetSuccessView(TemplateView):
    template_name = "password_reset_success.html"
