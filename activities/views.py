from django.db.models import Count, F, Sum, Window
from django.db.models.functions import Rank
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from activities.models.base import Activity, UserAnswer
from activities.serializers import (
    ActivitySerializer,
    LeaderboardEntrySerializer,
    UserAnswerSerializer,
)
from activities.services import AnswerSubmissionService
from users.models import User


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
            "Retorna los 10 estudiantes con mayor puntaje acumulado. "
            "Una actividad aporta sus puntos una sola vez por usuario, "
            "siempre que exista al menos una respuesta válida (is_correct=True). "
            "Siempre retorna la posición del usuario autenticado."
        ),
        responses={200: LeaderboardEntrySerializer(many=True)},
    )
    def get(self, request):
        user = request.user if request.user.is_authenticated else None

        pairs = (
            UserAnswer.objects.filter(is_correct=True)
            .values("user", "activity")
            .distinct()
            .annotate(points=F("activity__points"))
        )

        leaderboard_all = (
            pairs.values("user")
            .annotate(
                total_points=Sum("points"),
                activities_count=Count("activity"),
            )
            .annotate(
                position=Window(
                    expression=Rank(),
                    order_by=(F("total_points").desc(), F("user").asc()),
                )
            )
            .order_by(F("total_points").desc(), F("user").asc())
        )

        top10 = list(leaderboard_all[:10])

        extra_row = None
        if user:
            in_top = any(r["user"] == user.id for r in top10)
            if not in_top:
                extra_row = leaderboard_all.filter(user=user.id).first()
                if extra_row:
                    top10.append(extra_row)

        user_ids = [r["user"] for r in top10]
        users = User.objects.filter(id__in=user_ids).only(
            "id", "username", "first_name", "last_name"
        )
        users_map = {u.id: u for u in users}

        payload = []
        for row in top10:
            u = users_map.get(row["user"])
            payload.append({
                "user_id": row["user"],
                "username": getattr(u, "username", ""),
                "full_name": f"{u.first_name} {u.last_name}".strip() if u else "",
                "total_points": row["total_points"] or 0,
                "activities_count": row["activities_count"],
                "position": row["position"],
            })

        return Response(
            LeaderboardEntrySerializer(payload, many=True).data,
            status=status.HTTP_200_OK,
        )
