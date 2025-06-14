from rest_framework import serializers

from activities.models.choice import Choice, ChoiceActivity

from .base import ActivityListSerializer


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text"]


class ChoiceActivitySerializer(ActivityListSerializer, serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    payload = serializers.SerializerMethodField()

    class Meta:
        model = ChoiceActivity
        fields = ActivityListSerializer.Meta.fields

    def get_type(self, obj):
        return "multiple_choice"

    def get_payload(self, obj):
        choices = ChoiceSerializer(obj.choices.all(), many=True).data
        return {"choices": choices, "is_multiple": obj.is_multiple}
