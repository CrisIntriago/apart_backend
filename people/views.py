from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import Vocabulary
from content.serializers import VocabularySerializer
from people.models import Student

from .serializers import StudentDescriptionUpdateSerializer, StudentProfileSerializer


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
        if not person or not getattr(person, "student", None):
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
