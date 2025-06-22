from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import StudentProfileSerializer


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
