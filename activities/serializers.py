from rest_framework import serializers

from .models.base import Activity, ExamActivity, UserAnswer
from .models.choice import Choice
from .models.matching import MatchingPair
from .strategies.payload.registry import PayloadStrategyRegistry


class ActivitySerializer(serializers.ModelSerializer):
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
        raise NotImplementedError(
            "No payload strategy found for activity type: {}".format(obj.type)
        )


class ExamActivityItemSerializer(serializers.ModelSerializer):
    activity = ActivitySerializer()

    class Meta:
        model = ExamActivity
        fields = ("activity", "required", "position")


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


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ["is_correct"]


class LeaderboardEntrySerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.CharField()
    total_points = serializers.IntegerField()
    activities_count = serializers.IntegerField()
    position = serializers.IntegerField()
