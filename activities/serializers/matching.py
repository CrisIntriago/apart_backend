from rest_framework import serializers

from activities.models.matching import MatchingActivity, MatchingPair

from .base import ActivityListSerializer


class MatchingPairSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchingPair
        fields = ["left", "right"]


class MatchingActivitySerializer(ActivityListSerializer, serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    payload = serializers.SerializerMethodField()

    class Meta:
        model = MatchingActivity
        fields = [
            "id",
            "type",
            "title",
            "instructions",
            "difficulty",
            "created_at",
            "payload",
        ]

    def get_type(self, obj):
        return "matching"

    def get_payload(self, obj):
        pairs = MatchingPairSerializer(obj.pairs.all(), many=True).data
        return {"pairs": pairs}
