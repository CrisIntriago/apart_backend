from .base import StrategyInterface


class ChoiceStrategy(StrategyInterface):
    def validate(self, activity, selected: list[int]) -> bool:
        correct_ids = set(activity.choices.filter(is_correct=True).values_list('id', flat=True))
        selected_ids = set(selected)
        if not activity.is_multiple and len(selected_ids) > 1:
            return False
        return correct_ids == selected_ids
