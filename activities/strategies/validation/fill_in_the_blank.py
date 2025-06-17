from activities.models.base import ActivityType
from activities.models.fill_in_the_blank import FillInTheBlankActivity
from activities.serializers import FillInTheBlankAnswerInputSerializer

from .base import ValidationStrategy
from .registry import ValidationStrategyRegistry


@ValidationStrategyRegistry.register(
    ActivityType.FILL, FillInTheBlankAnswerInputSerializer
)
class FillInTheBlankValidationStrategy(ValidationStrategy):
    def validate(self, activity: FillInTheBlankActivity, user_response: dict) -> bool:
        expected_answers = activity.correct_answers
        user_answers = user_response.get("answers", {})

        if set(expected_answers.keys()) != set(user_answers.keys()):
            return False

        for index, correct in expected_answers.items():
            if user_answers.get(index, "").strip().lower() != correct.strip().lower():
                return False

        return True
