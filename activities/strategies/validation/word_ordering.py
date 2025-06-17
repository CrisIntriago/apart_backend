from activities.models.base import Activity, ActivityType
from activities.models.word_ordering import WordOrderingActivity
from activities.serializers import WordOrderingAnswerInputSerializer

from .base import ValidationStrategy
from .registry import ValidationStrategyRegistry


@ValidationStrategyRegistry.register(
    ActivityType.ORDER, WordOrderingAnswerInputSerializer
)
class WordOrderingValidationStrategy(ValidationStrategy):
    def validate(self, activity: Activity, user_response: dict) -> bool:
        activity = WordOrderingActivity.objects.get(id=activity.pk)
        correct_order = activity.sentence.strip().split()
        user_order = user_response.get("words", [])

        return correct_order == user_order
