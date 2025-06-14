from rest_framework import serializers

from activities.models.word_ordering import WordOrderingActivity

from .base import ActivityListSerializer


class WordOrderingActivitySerializer(
    ActivityListSerializer, serializers.ModelSerializer
):
    type = serializers.SerializerMethodField()
    payload = serializers.SerializerMethodField()

    class Meta:
        model = WordOrderingActivity
        fields = ActivityListSerializer.Meta.fields

    def get_type(self, obj):
        return "word_ordering"

    def get_payload(self, obj):
        words = obj.sentence.strip().split()
        return {"words": words}
