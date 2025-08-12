from django.contrib.auth import login
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User
from .serializers import LoginSerializer, RegisterSerializer, EmailValidationSerializer
from content.serializers import CourseSerializer
from .services import login_user, register_token, register_user


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: None},
        summary="Registro de usuario",
        description="Registra un nuevo usuario y devuelve su token",
    )
    def post(self, request):
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
        request=LoginSerializer,
        responses={200: None},
        summary="Inicio de sesión",
        description="Inicia sesión con un usuario y devuelve su token",
        auth=[]
    )
    def post(self, request):
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
        description="Verifica si un correo electrónico ya está registrado en el sistema.",
        auth=[]
    )
    def post(self, request):
        serializer = EmailValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        exists = User.objects.filter(email__iexact=email).exists()
        return Response({"exists": exists}, status=status.HTTP_200_OK)
