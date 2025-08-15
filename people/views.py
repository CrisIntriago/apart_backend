from django.db import transaction
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import Vocabulary
from content.serializers import VocabularySerializer
from people.models import Person, Student
from subscriptions.models import PlanChoices, Subscription
from users.models import User

from .serializers import (
    StudentDescriptionUpdateSerializer,
    StudentProfileSerializer,
    UpdateAccessSerializer,
)


class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Obtener perfil de estudiante",
        description="Devuelve el perfil del estudiante asociado al usuario autenticado.",  # noqa: E501
        responses={
            200: StudentProfileSerializer,
            400: "No hay perfil de personas asociado.",
        },
    )
    def get(self, request):
        person = getattr(request.user, "person", None)
        if not person:
            return Response(
                {"detail": "No hay perfil de persona asociado."},
                status=400,
            )
        serializer = StudentProfileSerializer(person, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        person = getattr(request.user, "person", None)
        if not person or not getattr(person, "student", None):
            return Response(
                {"detail": "No hay perfil de estudiante asociado."},
                status=400,
            )

        in_serializer = StudentDescriptionUpdateSerializer(data=request.data)
        in_serializer.is_valid(raise_exception=True)

        student = person.student
        student.description = in_serializer.validated_data["description"]
        student.save(update_fields=["description"])

        out_serializer = StudentProfileSerializer(person, context={"request": request})
        return Response(out_serializer.data, status=200)


class UpdateAccessView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Actualizar acceso",
        description=(
            "Actualiza el estado de acceso del usuario. "
            "User y Person deben existir. "
            "Solo crea Student si el plan es válido; asigna una descripción por defecto."  # noqa: E501
        ),
        request=UpdateAccessSerializer,
        responses={200: "Acceso actualizado.", 400: "Solicitud inválida."},
    )
    @transaction.atomic
    def post(self, request):
        serializer = UpdateAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = (request.data.get("email") or "").strip().lower()
        if not email:
            return Response(
                {"detail": "Email requerido."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "No existe un usuario con ese email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        person = Person.objects.filter(user=user).first()
        if not person:
            return Response(
                {"detail": "No hay perfil de persona asociado a ese usuario."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        person.has_access = serializer.validated_data["hasAccess"]
        person.save(update_fields=["has_access"])

        plan_type = request.data.get("planType")
        valid_plans = {choice.value for choice in PlanChoices}
        plan_is_valid = plan_type in valid_plans

        if plan_is_valid:
            student, created_student = Student.objects.get_or_create(
                person=person,
                defaults={
                    "description": "Estoy emocionado de comenzar mi aprendizaje en Apart y alcanzar mis metas."  # noqa: E501
                },
            )
            if person.has_access:
                Subscription.objects.get_or_create(
                    student=student,
                    defaults={"plan": plan_type},
                )

        return Response(
            {"detail": "Acceso actualizado", "has_access": person.has_access},
            status=status.HTTP_200_OK,
        )


class MyVocabularyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Obtener mi vocabulario",
        description="Devuelve la lista de palabras y significados del estudiante autenticado.",  # noqa: E501
        responses={200: VocabularySerializer(many=True)},
        examples=[
            OpenApiExample(
                "Example response",
                value=[
                    {
                        "id": 1,
                        "word": "apple",
                        "meaning": "manzana",
                        "difficulty": "easy",
                    },
                    {
                        "id": 2,
                        "word": "book",
                        "meaning": "libro",
                        "difficulty": "medium",
                    },
                ],
            )
        ],
    )
    def get(self, request):
        try:
            student_id = (
                Student.objects.only("id", "person__id")
                .values_list("id", flat=True)
                .get(person__user_id=request.user.id)
            )
        except Student.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)

        vocabularies = Vocabulary.objects.filter(student_id=student_id).order_by("word")
        serializer = VocabularySerializer(vocabularies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
