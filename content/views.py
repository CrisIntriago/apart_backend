from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from activities.serializers import ActivitySerializer

from .models import Course
from .serializers import CourseSerializer, ModuleSerializer


class CourseListView(APIView):
    @extend_schema(
        summary="Listar todos los cursos (sin módulos)",
        responses=CourseSerializer(many=True),
    )
    def get(self, request):
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True, context={"request": request})
        return Response(serializer.data)


class CourseModulesView(APIView):
    @extend_schema(
        summary="Obtener los módulos de un curso", responses=ModuleSerializer(many=True)
    )
    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        modules = course.modules.all()
        serializer = ModuleSerializer(modules, many=True, context={"request": request})
        return Response(serializer.data)


class CourseModuleActivitiesView(APIView):
    @extend_schema(
        summary="Obtener las actividades de un módulo",
        responses=ModuleSerializer(many=True),
    )
    def get(self, request, pk, module_pk):
        course = get_object_or_404(Course, pk=pk)
        module = get_object_or_404(course.modules, pk=module_pk)
        activities = module.activities.all()
        serializer = ActivitySerializer(
            activities, many=True, context={"request": request}
        )
        return Response(serializer.data)
