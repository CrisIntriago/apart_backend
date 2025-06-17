from activities.models.base import ActivityType
from activities.models.word_ordering import WordOrderingActivity

from .base import PayloadStrategy
from .registry import PayloadStrategyRegistry


@PayloadStrategyRegistry.register(ActivityType.ORDER)
class WordOrderingPayloadStrategy(PayloadStrategy):
    def get_payload(self, obj):
        obj = WordOrderingActivity.objects.get(pk=obj.pk)
        words = obj.sentence.strip().split()
        return {"words": words}
