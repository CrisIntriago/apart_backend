from activities.models.base import Activity
from activities.models.choice import ChoiceActivity
from activities.serializers import ChoiceAnswerInputSerializer
from utils.enums import ActivityType

from .base import ValidationStrategy
from .registry import ValidationStrategyRegistry


@ValidationStrategyRegistry.register(ActivityType.CHOICE, ChoiceAnswerInputSerializer)
class ChoiceValidationStrategy(ValidationStrategy):
    @classmethod
    def _validate(cls, activity: Activity, selected_ids: list[int]) -> bool:
        correct_choices = activity.choices.filter(is_correct=True).values_list(
            "id", flat=True
        )
        if activity.is_multiple:
            return set(selected_ids) == set(correct_choices)
        return len(selected_ids) == 1 and selected_ids[0] in correct_choices

    def validate(self, activity: Activity, user_response: dict) -> bool:
        activity = ChoiceActivity.objects.get(id=activity.id)
        selected_ids = user_response.get("selected_ids", [])
        return self._validate(activity, selected_ids)
