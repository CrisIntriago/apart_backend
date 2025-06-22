from rest_framework import serializers

from languages.serializers import LanguageSerializer
from people.models import Person, StudentLanguageProficiency


class StudentLanguageProficiencySerializer(serializers.ModelSerializer):
    language = serializers.SerializerMethodField()

    class Meta:
        model = StudentLanguageProficiency
        fields = ("language", "level")

    def get_language(self, obj):
        return LanguageSerializer(obj.language, context=self.context).data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["level"] = instance.get_level_display()
        return representation


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = (
            "id",
            "first_name",
            "last_name",
            "date_of_birth",
            "photo",
            "country",
        )


class StudentProfileSerializer(ProfileSerializer):
    languages = StudentLanguageProficiencySerializer(
        many=True,
        read_only=True,
        source="student.language_proficiencies",
    )

    class Meta(ProfileSerializer.Meta):
        model = Person
        fields = ProfileSerializer.Meta.fields + ("languages",)
