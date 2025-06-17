from activities.models.base import Activity, ActivityType
from activities.models.matching import MatchingActivity

from .base import ValidationStrategy
from .registry import ValidationStrategyRegistry


@ValidationStrategyRegistry.register(ActivityType.MATCH)
class MatchingValidationStrategy(ValidationStrategy):
    def validate(self, activity: Activity, user_response: dict) -> bool:
        activity = MatchingActivity.objects.get(id=activity.pk)
        correct_pairs = {pair.left: pair.right for pair in activity.pairs.all()}
        user_pairs = user_response.get("pairs", {})

        return correct_pairs == user_pairs
