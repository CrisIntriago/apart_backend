from rest_framework import serializers

from activities.models.base import ActivityType
from activities.serializers.choice import ChoiceActivitySerializer
from activities.serializers.fill_in_the_blank import FillInTheBlankActivitySerializer
from activities.serializers.matching import MatchingActivitySerializer
from activities.serializers.word_ordering import WordOrderingActivitySerializer

SERIALIZER_MAP = {
    ActivityType.CHOICE: ChoiceActivitySerializer,
    ActivityType.FILL: FillInTheBlankActivitySerializer,
    ActivityType.MATCH: MatchingActivitySerializer,
    ActivityType.ORDER: WordOrderingActivitySerializer,
}


class ActivityUnionSerializer(serializers.Serializer):
    type = serializers.CharField()

    def to_representation(self, instance):
        serializer_class = SERIALIZER_MAP.get(instance.type)
        if not serializer_class:
            raise ValueError(f"No serializer found for type {instance.type}")
        return serializer_class(instance).data
