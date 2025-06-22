from rest_framework import serializers

from languages.serializers import LanguageSerializer

from .models import Course, Module


class ModuleSerializer(serializers.ModelSerializer):
    difficulty = serializers.CharField(source="get_difficulty_display")

    class Meta:
        model = Module
        fields = ("id", "name", "description", "image", "difficulty")


class CourseSerializer(serializers.ModelSerializer):
    difficulty = serializers.CharField(source="get_difficulty_display")
    language = LanguageSerializer(read_only=True)

    class Meta:
        model = Course
        fields = ("id", "name", "description", "image", "difficulty", "language")
