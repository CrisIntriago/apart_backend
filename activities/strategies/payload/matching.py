from random import shuffle

from activities.models.matching import MatchingActivity
from activities.strategies.payload.base import PayloadStrategy
from activities.strategies.payload.registry import PayloadStrategyRegistry
from utils.enums import ActivityType


@PayloadStrategyRegistry.register(ActivityType.MATCH)
class MatchingPayloadStrategy(PayloadStrategy):
    def get_payload(self, obj):
        obj = MatchingActivity.objects.get(pk=obj.pk)
        pairs = list(obj.pairs.all())

        left_items = [pair.left for pair in pairs]
        right_items = [pair.right for pair in pairs]

        shuffle(left_items)
        shuffle(right_items)

        mixed_pairs = [
            {"left": left, "right": right}
            for left, right in zip(left_items, right_items)
        ]

        return {"pairs": mixed_pairs}
