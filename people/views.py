from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import Vocabulary
from content.serializers import VocabularySerializer
from people.models import Student

from .serializers import (
    StudentDescriptionUpdateSerializer,
    StudentProfileSerializer,
    UpdateAccessSerializer,
)
from subscriptions.models import Subscription, PlanChoices


class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Obtener perfil de estudiante",
        description="Devuelve el perfil del estudiante asociado al usuario autenticado.",  # noqa: E501
        responses={
            200: StudentProfileSerializer,
            400: "No hay perfil de estudiante asociado.",
        },
    )
    def get(self, request):
        person = getattr(request.user, "person", None)
        if not person:
            return Response(
                {"detail": "No hay perfil de persona asociado."},
                status=400,
            )
        student = getattr(person, "student", None)
        if not student:
            return Response(
                {"detail": "No hay perfil de estudiante asociado."},
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
    #TO-DO Que solo pueda enviar eso el frontend con CROSS  origin para futuro.
    permission_classes = []

    @extend_schema(
        summary="Actualizar acceso",
        description="Actualiza el estado de acceso del usuario autenticado.",
        request=UpdateAccessSerializer,
        responses={
            200: "Acceso actualizado.",
            400: "Solicitud inválida.",
        },
    )
    def post(self, request):
        import logging
        logger = logging.getLogger("django")
        logger.info(f"POST /api/people/update-access body: {request.data}")

        serializer = UpdateAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.data.get("email")
        logger.info(f"Email recibido: {email}")
        if not email:
            logger.warning("No se recibió email en la petición.")
            return Response({"detail": "Email requerido."}, status=400)
        from people.models import Person
        person = Person.objects.filter(user__email=email).first()
        logger.info(f"Persona encontrada: {person}")
        if not person:
            logger.warning(f"No hay perfil de persona asociado a {email}")
            return Response({"detail": "No hay perfil de persona asociado a ese correo."}, status=400)
        person.has_access = serializer.validated_data["hasAccess"]
        person.save()
        logger.info(f"Acceso actualizado para {person}. has_access={person.has_access}")

        student = getattr(person, "student", None)
        logger.info(f"Student asociado: {student}")
        plan_type = request.data.get("planType")
        logger.info(f"PlanType recibido: {plan_type}")
        if person.has_access and student and plan_type in [PlanChoices.MONTHLY, PlanChoices.ANNUAL]:
            # Solo crear si no existe
            if not hasattr(student, "subscription"):
                Subscription.objects.create(
                    student=student,
                    plan=plan_type,
                )
                logger.info(f"Subscription creada para {student} con plan {plan_type}")
            else:
                logger.info(f"El student {student} ya tiene una suscripción")

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
