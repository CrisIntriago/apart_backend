from rest_framework import serializers

from content.serializers import CourseSerializer
from languages.serializers import LanguageSerializer
from people.models import Person, StudentLanguageProficiency


class StudentLanguageProficiencySerializer(serializers.ModelSerializer):
    language = LanguageSerializer(read_only=True)

    class Meta:
        model = StudentLanguageProficiency
        fields = ("language", "level")

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
    course = CourseSerializer(read_only=True, source="student.course")

    class Meta(ProfileSerializer.Meta):
        model = Person
        fields = ProfileSerializer.Meta.fields + ("languages", "course")
