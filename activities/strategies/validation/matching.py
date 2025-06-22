from activities.models.base import Activity
from activities.models.matching import MatchingActivity
from activities.serializers import MatchingAnswerInputSerializer
from utils.enums import ActivityType

from .base import ValidationStrategy
from .registry import ValidationStrategyRegistry


@ValidationStrategyRegistry.register(ActivityType.MATCH, MatchingAnswerInputSerializer)
class MatchingValidationStrategy(ValidationStrategy):
    def validate(self, activity: Activity, user_response: dict) -> bool:
        activity = MatchingActivity.objects.get(id=activity.pk)
        correct_pairs = {pair.left: pair.right for pair in activity.pairs.all()}
        user_pairs = user_response.get("pairs", {})

        return correct_pairs == user_pairs
