from django.shortcuts import get_object_or_404

from activities.models.base import Activity, UserAnswer
from activities.strategies.validation.registry import ValidationStrategyRegistry


class AnswerSubmissionService:
    def __init__(self, user, activity_id, input_data):
        self.user = user
        self.activity_id = activity_id
        self.input_data = input_data

    def execute(self):
        activity = self._get_activity()
        serializer = self._get_validated_serializer(activity)
        is_correct = self._validate_response(activity, serializer.validated_data)
        return self._save_user_answer(activity, serializer.validated_data, is_correct)

    def _get_activity(self):
        return get_object_or_404(Activity, pk=self.activity_id)

    def _get_validated_serializer(self, activity):
        serializer_class = ValidationStrategyRegistry.get_serializer(activity.type)
        if serializer_class is None:
            raise ValueError(f"No serializer para tipo '{activity.type}'")
        serializer = serializer_class(data=self.input_data)
        serializer.is_valid(raise_exception=True)
        self.validated_data = serializer.validated_data
        return serializer

    def _validate_response(self, activity, validated_data):
        strategy = ValidationStrategyRegistry.get_strategy(activity.type)
        if strategy is None:
            raise ValueError(f"No estrategia para tipo '{activity.type}'")
        return strategy.validate(activity, validated_data)

    def _save_user_answer(self, activity, response_data, is_correct):
        return UserAnswer.objects.create(
            user=self.user,
            activity_type=activity.type,
            activity=activity,
            response_data=response_data,
            is_correct=is_correct,
        )
