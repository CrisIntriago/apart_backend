from rest_framework import serializers


class ActivityListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    title = serializers.CharField()
    instructions = serializers.CharField(allow_blank=True)
    difficulty = serializers.CharField()
    created_at = serializers.DateTimeField()
    payload = serializers.DictField()

    class Meta:
        fields = (
            "id",
            "type",
            "title",
            "instructions",
            "difficulty",
            "created_at",
            "payload",
        )
