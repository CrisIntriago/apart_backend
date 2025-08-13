from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
)
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from activities.models.base import ExamActivity
from activities.serializers import ActivitySerializer, ExamActivityItemSerializer
from activities.services import AnswerSubmissionService
from people.serializers import StudentProfileSerializer

from .models import Course, Exam, ExamAttempt, ExamAttemptStatus
from .permissions import HasStartedExam
from .serializers import (
    CourseSerializer,
    ExamSerializer,
    FinishAttemptRequestSerializer,
    FinishAttemptResponseSerializer,
    ModuleSerializer,
)
from .services import ExamGradingService


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


class CourseStudentsView(APIView):
    @extend_schema(
        summary="Obtener los estudiantes de un curso",
        responses=StudentProfileSerializer(many=True),
    )
    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        students = course.students.select_related("person").all()
        persons = [student.person for student in students if student.person]
        serializer = StudentProfileSerializer(
            persons, many=True, context={"request": request}
        )
        return Response(serializer.data)


class CourseExamsView(APIView):
    @extend_schema(
        summary="Obtener los exámenes publicados de un curso",
        responses={200: ExamSerializer(many=True)},
        examples=[
            OpenApiExample(
                name="Respuesta exitosa",
                value={
                    "id": 1,
                    "course": 1,
                    "type": "MIDTERM",
                    "title": "Soy examen",
                    "description": "Upa",
                    "is_published": True,
                    "time_limit_minutes": 30,
                    "attempts_allowed": 1,
                    "pass_mark_percent": 60,
                },
                response_only=True,
            )
        ],
    )
    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        exams = course.exams.filter(is_published=True)
        serializer = ExamSerializer(exams, many=True, context={"request": request})
        return Response(serializer.data)


class StartAttemptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Iniciar intento de examen",
        description="Crea un nuevo intento para un examen si el usuario aún tiene intentos disponibles.",  # noqa: E501
        parameters=[
            OpenApiParameter(
                name="exam_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID del examen",
            )
        ],
        responses={
            201: {
                "example": {
                    "attempt_id": 12,
                    "attempt_number": 1,
                    "time_limit_minutes": 30,
                    "status": "IN_PROGRESS",
                    "started_at": "2025-08-12T14:30:00Z",
                }
            },
            400: {"example": {"detail": "No attempts remaining."}},
        },
    )
    def post(self, request, exam_id: int):
        exam = Exam.objects.get(pk=exam_id)
        user = request.user

        used = ExamAttempt.objects.filter(
            exam=exam,
            user=user,
            status__in=[
                ExamAttemptStatus.GRADED,
                ExamAttemptStatus.EXPIRED,
                ExamAttemptStatus.CANCELLED,
            ],
        ).count()

        if exam.attempts_allowed and used >= exam.attempts_allowed:
            return Response({"detail": "No attempts remaining."}, status=400)

        next_number = (
            ExamAttempt.objects.filter(exam=exam, user=user).aggregate(
                m=Max("attempt_number")
            )["m"]
            or 0
        ) + 1

        attempt = ExamAttempt.objects.create(
            exam=exam,
            user=user,
            attempt_number=next_number,
            time_limit_minutes=exam.time_limit_minutes,
            status=ExamAttemptStatus.IN_PROGRESS,
        )
        return Response(
            {
                "attempt_id": attempt.id,
                "attempt_number": attempt.attempt_number,
                "time_limit_minutes": attempt.time_limit_minutes,
                "status": attempt.status,
                "started_at": attempt.started_at,
            },
            status=201,
        )


class ExamActivitiesView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasStartedExam]

    def get_object(self, exam_id):
        return get_object_or_404(Exam, pk=exam_id, is_published=True)

    @extend_schema(
        summary="Obtener actividades de un examen",
        description="Devuelve la lista de actividades asociadas a un examen publicado. Usa `shuffle` para barajar el orden.",  # noqa: E501
        parameters=[
            OpenApiParameter(
                name="shuffle",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Si es true, retorna las actividades en orden aleatorio. Acepta "1/true/True".',  # noqa: E501
            ),
        ],
        responses=ExamActivityItemSerializer(many=True),
        examples=[
            OpenApiExample(
                "Ejemplo",
                value={
                    "activity": {
                        "id": 101,
                        "type": "choice",
                        "title": "Select the correct option",
                        "instructions": "Choose one answer.",
                        "difficulty": "medium",
                        "created_at": "2025-08-13T00:51:52.839102Z",
                        "payload": {
                            "choices": [
                                {"id": 1, "text": "Option A"},
                                {"id": 2, "text": "Option B"},
                            ],
                            "is_multiple": False,
                        },
                    },
                    "required": True,
                    "position": 0,
                },
            )
        ],
    )
    def get(self, request, exam_id: int):
        exam = self.get_object(exam_id)
        self.check_object_permissions(request, exam)

        qs = ExamActivity.objects.select_related("activity").filter(exam=exam)

        shuffle = request.query_params.get("shuffle")
        if shuffle in ("1", "true", "True"):
            qs = list(qs)
            import random

            random.shuffle(qs)

        data = ExamActivityItemSerializer(
            qs, many=True, context={"request": request}
        ).data
        return Response(data, status=status.HTTP_200_OK)


class FinishAttemptAndSubmitAnswersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, attempt_id: int):
        attempt = ExamAttempt.objects.select_related("exam").get(pk=attempt_id)
        if attempt.user_id != request.user.id:
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        req_ser = FinishAttemptRequestSerializer(
            data=request.data, context={"attempt": attempt}
        )
        req_ser.is_valid(raise_exception=True)
        answers = req_ser.validated_data["answers"]

        AnswerSubmissionService.submit_many(
            user=request.user,
            answers_payload=answers,
            exam_attempt=attempt,
        )

        if attempt.is_expired():
            attempt.status = ExamAttemptStatus.EXPIRED
            attempt.finished_at = attempt.finished_at or timezone.now()
            attempt.save(update_fields=["status", "finished_at"])

        graded = ExamGradingService.finalize_and_grade(attempt.id)

        resp_ser = FinishAttemptResponseSerializer(graded)

        return Response(resp_ser.data, status=status.HTTP_200_OK)
