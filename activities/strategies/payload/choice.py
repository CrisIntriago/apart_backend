from activities.models.choice import ChoiceActivity
from activities.serializers import ChoiceSerializer
from activities.strategies.payload.base import PayloadStrategy
from activities.strategies.payload.registry import PayloadStrategyRegistry
from utils.enums import ActivityType


@PayloadStrategyRegistry.register(ActivityType.CHOICE)
class ChoicePayloadStrategy(PayloadStrategy):
    def get_payload(self, obj):
        obj = ChoiceActivity.objects.get(pk=obj.pk)
        choices = ChoiceSerializer(obj.choices.all(), many=True).data
        return {"choices": choices, "is_multiple": obj.is_multiple}
