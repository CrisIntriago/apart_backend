from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiRequest,
    OpenApiResponse,
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
from utils.enums import CONSUME_STATUSES

from .exceptions import NoAttemptsRemainingError
from .models import Course, Exam, ExamAttempt, ExamAttemptStatus
from .permissions import HasStartedExam
from .serializers import (
    CourseProgressSerializer,
    CourseSerializer,
    ExamAttemptStartSerializer,
    ExamSerializer,
    FinishAttemptRequestSerializer,
    FinishAttemptResponseSerializer,
    ModuleSerializer,
)
from .services import CourseProgressService, ExamAttemptService, ExamGradingService


class CourseListView(APIView):
    @extend_schema(
        summary="Listar todos los cursos (sin módulos)",
        responses=CourseSerializer(many=True),
    )
    def get(self, request):
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True, context={"request": request})
        return Response(serializer.data)


class CourseProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Courses"],
        summary="Avance de un curso (usuario autenticado)",
        description=(
            "Devuelve el porcentaje de avance del curso para el usuario autenticado, "
            "contando actividades con al menos una respuesta. Incluye desglose por módulo."  # noqa: E501
        ),
        parameters=[
            OpenApiParameter(
                name="course_id",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            ),
        ],
        responses={200: CourseProgressSerializer},
    )
    def get(self, request, course_id: int):
        course = get_object_or_404(Course, id=course_id)
        result = CourseProgressService(course=course, user=request.user).compute()

        serializer = CourseProgressSerializer({
            "course": {"id": course.id, "name": course.name},
            "overall": result.overall,
            "modules": result.modules,
        })
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
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Exams"],
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
                    "attempts_allowed": 3,
                    "pass_mark_percent": 60,
                    "has_attempts_left": True,
                    "remaining_attempts": 2,
                    "user_last_attempt_at": "2025-08-10T15:32:21Z",
                    "user_percentage": "82.50",
                    "user_passed": True,
                },
                response_only=True,
            )
        ],
    )
    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)

        graded_or_expired_qs = (
            ExamAttempt.objects.filter(
                user_id=request.user.id,
                status__in=[ExamAttemptStatus.GRADED, ExamAttemptStatus.EXPIRED],
            )
            .only("exam_id", "percentage", "passed", "graded_at", "finished_at")
            .order_by("-percentage", "-graded_at")
        )

        exams = (
            course.exams.filter(is_published=True)
            .annotate(
                user_used_attempts_count=Count(
                    "attempts",
                    filter=Q(
                        attempts__user_id=request.user.id,
                        attempts__status__in=CONSUME_STATUSES,
                    ),
                    distinct=True,
                ),
                user_in_progress_count=Count(
                    "attempts",
                    filter=Q(
                        attempts__user_id=request.user.id,
                        attempts__status=ExamAttemptStatus.IN_PROGRESS,
                    ),
                    distinct=True,
                ),
            )
            .prefetch_related(
                Prefetch(
                    "attempts",
                    queryset=graded_or_expired_qs,
                    to_attr="user_graded_attempts",
                )
            )
        )

        serializer = ExamSerializer(exams, many=True, context={"request": request})
        return Response(serializer.data)


class StartAttemptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Exams"],
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
        try:
            result = ExamAttemptService.start_attempt(
                exam_id=exam_id, user=request.user
            )
        except NoAttemptsRemainingError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ExamAttemptStartSerializer(instance=result.attempt)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if result.created else status.HTTP_200_OK,
        )


class ExamActivitiesView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasStartedExam]

    def get_object(self, exam_id):
        return get_object_or_404(Exam, pk=exam_id, is_published=True)

    @extend_schema(
        tags=["Exams"],
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

    @extend_schema(
        tags=["Exams"],
        summary="Finalizar intento y enviar respuestas",
        description="Recibe las respuestas del usuario para un examen y finaliza el intento.",  # noqa: E501
        parameters=[
            OpenApiParameter(
                name="attempt_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="ID del intento de examen",
            )
        ],
        request=OpenApiRequest(
            request=FinishAttemptRequestSerializer,
            examples=[
                OpenApiExample(
                    "Solicitud simple",
                    value={
                        "answers": [
                            {"activity_id": 1, "input_data": {"selected_ids": [2]}}
                        ]
                    },
                )
            ],
        ),
        responses={
            200: OpenApiResponse(
                response=FinishAttemptResponseSerializer,
                examples=[
                    OpenApiExample(
                        "Respuesta simple",
                        value={
                            "attempt_id": 10,
                            "exam_id": 5,
                            "status": "PASSED",
                            "score_points": 8,
                            "max_points": 10,
                            "percentage": 80.0,
                            "passed": True,
                            "correct_count": 4,
                            "total_questions": 5,
                            "finished_at": "2025-08-12T15:30:00Z",
                        },
                    )
                ],
            )
        },
    )
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
