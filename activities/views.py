from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from activities.models.base import Activity
from activities.serializers import (
    ActivitySerializer,
    LeaderboardEntrySerializer,
    UserAnswerSerializer,
)
from activities.services import AnswerSubmissionService, LeaderboardService


class ActivityListView(APIView):
    @extend_schema(
        summary="Lista unificada de actividades",
        description="Devuelve una lista combinada de actividades de todos los tipos.",
        responses={200: ActivitySerializer(many=True)},
    )
    def get(self, request):
        activities = Activity.objects.all().order_by("created_at")
        serializer = ActivitySerializer(activities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Enviar respuesta de actividad",
        request=serializers.JSONField(),
        description="Permite a un usuario enviar una respuesta para una actividad específica.",  # noqa: E501
        responses={201: UserAnswerSerializer},
        examples=[
            OpenApiExample(
                name="Opción múltiple (choice)",
                description="Respuesta seleccionando varias opciones",
                value={"selected_ids": [3, 5]},
                request_only=True,
            ),
            OpenApiExample(
                name="Completar espacios (fill_in)",
                description="Respuestas para completar los espacios en blanco",
                value={"answers": {"0": "París", "1": "Ecuador"}},
                request_only=True,
            ),
            OpenApiExample(
                name="Unir pares (matching)",
                description="Asociaciones entre ítems de la izquierda y derecha",
                value={"pairs": {"manzana": "apple", "perro": "dog"}},
                request_only=True,
            ),
            OpenApiExample(
                name="Ordenar palabras (order)",
                description="Palabras ordenadas correctamente",
                value={"words": ["El", "gato", "está", "durmiendo"]},
                request_only=True,
            ),
        ],
    )
    def post(self, request, activity_id):
        try:
            service = AnswerSubmissionService(request.user, activity_id, request.data)
            user_answer = service.execute()
            serializer = UserAnswerSerializer(user_answer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LeaderboardTop10View(APIView):
    @extend_schema(
        summary="Top 10 de estudiantes por puntuación",
        description=(
            "Permite filtrar por ventana de tiempo (day, week, month, all) "
            "y por módulo (module_id)."
        ),
        parameters=[
            OpenApiParameter(
                name="time_window",
                required=False,
                description="day|week|month|all",
                type=str,
            ),
            OpenApiParameter(
                name="module_id", required=False, description="ID del módulo", type=int
            ),
        ],
        responses={200: LeaderboardEntrySerializer(many=True)},
    )
    def get(self, request):
        user_id = request.user.id if request.user.is_authenticated else None
        time_window = request.query_params.get("time_window", "all")
        module_id = request.query_params.get("module_id")

        module_id = (
            int(module_id)
            if module_id
            not in (
                None,
                "",
            )
            else None
        )

        service = LeaderboardService(
            request_user_id=user_id,
            limit=10,
            time_window=time_window,
            module_id=module_id,
        )
        payload = service.execute()
        return Response(
            LeaderboardEntrySerializer(payload, many=True).data,
            status=status.HTTP_200_OK,
        )
