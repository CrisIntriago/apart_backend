import uuid

import requests
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
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

from content.serializers import CourseSerializer
from people.models import Enrollment
from users.models import User
from utils.enums import EnrollmentStatus

from .exceptions import (
    PasswordValidationError,
    TokenExpired,
    TokenInvalid,
)
from .serializers import (
    EmailValidationSerializer,
    LoginGoogleSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    RegisterGoogleSerializer,
    RegisterSerializer,
)
from .services import PasswordResetService, login_user, register_token, register_user


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request={
            "application/json": RegisterSerializer,
            "application/json;google": RegisterGoogleSerializer,
        },
        responses={201: None},
        summary="Registro de usuario",
        description="Registra un nuevo usuario y devuelve su token (puede autenticarse usando google o email)",  # noqa: E501
    )
    def post(self, request):
        google_token = request.data.get("google_token")

        if google_token:
            try:
                url = f"https://oauth2.googleapis.com/tokeninfo?id_token={google_token}"
                response = requests.get(url)
                google_data = response.json()

                if response.status_code != 200 or "email" not in google_data:
                    return Response(
                        {"detail": ("Token de Google no válido.")},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                return Response(
                    {
                        "user": {
                            "email": google_data["email"],
                            "username": google_data["name"],
                            "photo": google_data["picture"],
                            "password": User.make_random_password(),
                        },
                        "token": "notokenyet",
                    },
                    status=status.HTTP_201_CREATED,
                )
            except requests.exceptions.RequestException:
                return Response(
                    {"detail": "Error al verificar el token de Google."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = register_user(serializer.validated_data)
        token = register_token(user)
        photo = user.person.photo if user.person.photo else None
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
                    "photo": photo,
                },
                "token": token,
            },
            status=status.HTTP_201_CREATED,
        )


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

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
                    return Response(
                        {"detail": ("Token de Google no válido.")},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

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
                                "photo": google_data["picture"],
                                "password": User.make_random_password(),
                            }
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )

                login(
                    request, user, backend="django.contrib.auth.backends.ModelBackend"
                )
                user = user_model.objects.get(email=email)
                token = login_user(user)
                courses_data = []
                person = getattr(user, "person", None)
                student = getattr(person, "student", None) if person else None

                if student:
                    now = timezone.now()
                    enrollments_qs = (
                        Enrollment.objects.filter(
                            student=student,
                            status=EnrollmentStatus.ACTIVE,
                        )
                        .filter(Q(start_at__isnull=True) | Q(start_at__lte=now))
                        .filter(Q(end_at__isnull=True) | Q(end_at__gte=now))
                        .select_related("course")
                    )

                    courses = [e.course for e in enrollments_qs if e.course is not None]

                    if not courses and getattr(student, "active_course", None):
                        courses = [student.active_course]

                    courses_data = CourseSerializer(courses, many=True).data
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
                return Response(
                    {"detail": ("Error al verificar el token de Google.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Login tradicional
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        token = login_user(user)
        courses_data = []
        person = getattr(user, "person", None)
        student = getattr(person, "student", None) if person else None

        if student:
            now = timezone.now()
            enrollments_qs = (
                Enrollment.objects.filter(
                    student=student,
                    status=EnrollmentStatus.ACTIVE,
                )
                .filter(Q(start_at__isnull=True) | Q(start_at__lte=now))
                .filter(Q(end_at__isnull=True) | Q(end_at__gte=now))
                .select_related("course")
            )

            courses = [e.course for e in enrollments_qs if e.course is not None]

            if not courses and getattr(student, "active_course", None):
                courses = [student.active_course]

            courses_data = CourseSerializer(courses, many=True).data

        photo = user.person.photo.url if user.person.photo and hasattr(user.person.photo, 'url') else None
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
                    "photo": photo,
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
                request, self.template_name, {"invalid": True, "reason": check.reason}
            )
        return render(request, self.template_name, {"token": token})

    def post(self, request, token):
        svc = PasswordResetService()
        try:
            svc.reset_with_token(self._parse(token), request.POST.get("password", ""))
        except TokenInvalid:
            return render(
                request, self.template_name, {"invalid": True, "reason": "not_found"}
            )
        except TokenExpired:
            return render(
                request, self.template_name, {"invalid": True, "reason": "expired"}
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
