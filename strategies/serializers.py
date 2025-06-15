from rest_framework import serializers


class AnswerSerializer(serializers.Serializer):
    activity_id = serializers.IntegerField()
    selected = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="Lista de IDs de opciones seleccionadas"
    )
