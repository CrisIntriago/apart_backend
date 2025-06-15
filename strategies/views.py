from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .serializers import AnswerSerializer
from .factory import get_strategy
from activities.models.choice import ChoiceActivity


class ValidateAnswerView(APIView):
    @extend_schema(
        request=AnswerSerializer,
        responses={200: AnswerSerializer, 400: 'Bad Request'}
    )
    def post(self, request):
        serializer = AnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        activity = ChoiceActivity.objects.get(pk=serializer.validated_data['activity_id'])
        strategy = get_strategy(activity.type)
        is_correct = strategy.validate(activity, serializer.validated_data['selected'])

        return Response({
            'activity_id': activity.id,
            'is_correct': is_correct
        }, status=status.HTTP_200_OK)
