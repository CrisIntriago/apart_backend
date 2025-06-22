from activities.models.fill_in_the_blank import FillInTheBlankActivity
from activities.strategies.payload.base import PayloadStrategy
from activities.strategies.payload.registry import PayloadStrategyRegistry
from utils.enums import ActivityType


@PayloadStrategyRegistry.register(ActivityType.FILL)
class FillInTheBlankPayloadStrategy(PayloadStrategy):
    def get_payload(self, obj):
        obj = FillInTheBlankActivity.objects.get(pk=obj.pk)
        return {"text": obj.text}
