from rest_framework import serializers

from activities.models.fill_in_the_blank import FillInTheBlankActivity

from .base import ActivityListSerializer


class FillInTheBlankActivitySerializer(
    ActivityListSerializer, serializers.ModelSerializer
):
    type = serializers.SerializerMethodField()
    payload = serializers.SerializerMethodField()

    class Meta:
        model = FillInTheBlankActivity
        fields = ActivityListSerializer.Meta.fields

    def get_type(self, obj):
        return "fill_in"

    def get_payload(self, obj):
        return {"text": obj.text}
