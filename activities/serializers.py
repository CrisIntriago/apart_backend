from rest_framework import serializers

from .models.base import Activity
from .models.choice import Choice
from .models.matching import MatchingPair
from .strategies.payload.registry import PayloadStrategyRegistry


class ActivityListSerializer(serializers.ModelSerializer):
    payload = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = (
            "id",
            "type",
            "title",
            "instructions",
            "difficulty",
            "created_at",
            "payload",
        )

    def get_payload(self, obj):
        strategy = PayloadStrategyRegistry.get_strategy(obj.type)
        if strategy:
            return strategy.get_payload(obj)
        raise NotImplementedError("No implementado")


class MatchingPairSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchingPair
        fields = ["left", "right"]


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text"]


class ChoiceAnswerInputSerializer(serializers.Serializer):
    selected_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )


class FillInTheBlankAnswerInputSerializer(serializers.Serializer):
    answers = serializers.DictField(child=serializers.CharField(allow_blank=False))


class MatchingAnswerInputSerializer(serializers.Serializer):
    pairs = serializers.DictField(child=serializers.CharField())


class WordOrderingAnswerInputSerializer(serializers.Serializer):
    words = serializers.ListField(child=serializers.CharField())
