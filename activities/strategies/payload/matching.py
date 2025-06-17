from activities.models.base import ActivityType
from activities.models.matching import MatchingActivity
from activities.serializers import MatchingPairSerializer
from activities.strategies.payload.base import PayloadStrategy
from activities.strategies.payload.registry import PayloadStrategyRegistry


@PayloadStrategyRegistry.register(ActivityType.MATCH)
class MatchingPayloadStrategy(PayloadStrategy):
    def get_payload(self, obj):
        obj = MatchingActivity.objects.get(pk=obj.pk)
        pairs = MatchingPairSerializer(obj.pairs.all(), many=True).data
        return {"pairs": pairs}
