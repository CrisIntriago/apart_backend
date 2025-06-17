from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Course
from .serializers import CourseSerializer, ModuleSerializer


class CourseListView(APIView):
    @extend_schema(
        summary="Listar todos los cursos (sin módulos)",
        responses=CourseSerializer(many=True),
    )
    def get(self, request):
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)


class CourseModulesView(APIView):
    @extend_schema(
        summary="Obtener los módulos de un curso", responses=ModuleSerializer(many=True)
    )
    def get(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response(
                {"detail": "Curso no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        modules = course.modules.all()
        serializer = ModuleSerializer(modules, many=True)
        return Response(serializer.data)
