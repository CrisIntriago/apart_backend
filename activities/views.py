# activities/views/unified.py
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from activities.models.base import Activity
from activities.serializers import ActivityListSerializer
from activities.services import AnswerSubmissionService


class ActivityListView(APIView):
    @extend_schema(
        summary="Lista unificada de actividades",
        description="Devuelve una lista combinada de actividades de todos los tipos.",
        responses={200: ActivityListSerializer(many=True)},
    )
    def get(self, request):
        activities = Activity.objects.all().order_by("created_at")
        serializer = ActivityListSerializer(activities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitAnswerView(APIView):
    def post(self, request, activity_id):
        try:
            service = AnswerSubmissionService(request.user, activity_id, request.data)
            is_correct = service.execute()
            return Response({"is_correct": is_correct}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
