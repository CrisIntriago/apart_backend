import requests
from django.contrib.auth import login, get_user_model, authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer
from .services import login_user, register_token, register_user


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
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

                email = google_data["email"]

                user, created = get_user_model().objects.get_or_create(email=email)

                if created:
                    user.username = google_data.get("name", email.split(
                        '@')[0])
                    user.save()

                token = register_token(user)

                return Response(
                    {
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "phone": user.phone,
                        },
                        "token": token,
                    },
                    status=status.HTTP_200_OK,
                )
            except requests.exceptions.RequestException:
                return Response({"detail": _("Error al verificar el token de Google.")}, status=status.HTTP_400_BAD_REQUEST)

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
                    "phone": user.phone,
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
        # Soporte para login con Google token
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
                    return Response({"detail": ("No existe un usuario registrado con este email.")}, status=status.HTTP_404_NOT_FOUND)

                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                token = login_user(user)
                return Response(
                    {
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "phone": user.phone,
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
        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone,
                },
                "token": token,
            },
            status=status.HTTP_200_OK,
        )
