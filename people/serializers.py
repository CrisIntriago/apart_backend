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
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Person
        fields = (
            "id",
            "first_name",
            "last_name",
            "date_of_birth",
            "photo",
            "country",
            "email",
        )


class StudentProfileSerializer(ProfileSerializer):
    description = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    has_access = serializers.SerializerMethodField()

    class Meta(ProfileSerializer.Meta):
        model = Person
        fields = ProfileSerializer.Meta.fields + (
            "description",
            "languages",
            "course",
            "has_access",
        )

    def get_description(self, obj):
        return getattr(getattr(obj, "student", None), "description", "") or ""

    def get_languages(self, obj):
        student = getattr(obj, "student", None)
        if student:
            return StudentLanguageProficiencySerializer(
                student.language_proficiencies.all(), many=True
            ).data
        return []

    def get_course(self, obj):
        student = getattr(obj, "student", None)
        if student and student.active_course:
            return CourseSerializer(student.active_course).data
        return None

    def get_has_access(self, obj):
        return getattr(getattr(obj, "student", None), "has_access", False)


class UpdateAccessSerializer(serializers.Serializer):
    hasAccess = serializers.BooleanField()
    email = serializers.EmailField()
    plan = serializers.CharField()


class StudentDescriptionUpdateSerializer(serializers.Serializer):
    description = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        required=True,
        max_length=2000,
        help_text="Descripción breve del estudiante.",
    )
