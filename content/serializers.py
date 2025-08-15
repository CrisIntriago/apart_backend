from typing import Any, Dict, List

from rest_framework import serializers

from activities.models.base import Activity
from activities.strategies.validation.registry import ValidationStrategyRegistry
from content.models import ExamAttempt
from languages.serializers import LanguageSerializer

from .models import Course, Exam, Module, Vocabulary


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


class ExamSerializer(serializers.ModelSerializer):
    has_attempts_left = serializers.SerializerMethodField()
    remaining_attempts = serializers.SerializerMethodField()
    user_last_attempt_at = serializers.SerializerMethodField()
    user_percentage = serializers.SerializerMethodField()
    user_passed = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = (
            "id",
            "course",
            "type",
            "title",
            "description",
            "is_published",
            "time_limit_minutes",
            "attempts_allowed",
            "pass_mark_percent",
            "has_attempts_left",
            "remaining_attempts",
            "user_last_attempt_at",
            "user_percentage",
            "user_passed",
        )

    def _allowed(self, obj) -> int | None:
        return obj.attempts_allowed

    def _used(self, obj) -> int:
        return getattr(obj, "user_used_attempts_count", 0) or 0

    def _user_attempts(self, obj):
        return getattr(obj, "user_graded_attempts", None)

    def get_remaining_attempts(self, obj):
        allowed = self._allowed(obj)
        if allowed is None:
            return None
        used = self._used(obj)
        return max(allowed - used, 0)

    def get_has_attempts_left(self, obj):
        remaining = self.get_remaining_attempts(obj)
        return True if remaining is None else remaining > 0

    def get_user_last_attempt_at(self, obj):
        attempts = self._user_attempts(obj)
        if not attempts:
            return None
        last = max(attempts, key=lambda a: (a.graded_at or a.finished_at))
        dt = last.graded_at or last.finished_at
        return dt.isoformat().replace("+00:00", "Z") if dt else None

    def get_user_percentage(self, obj):
        attempts = self._user_attempts(obj)
        if not attempts:
            return None
        best = attempts[0]
        return f"{best.percentage:.2f}" if best.percentage is not None else None

    def get_user_passed(self, obj):
        attempts = self._user_attempts(obj)
        return any(a.passed for a in (attempts or []))


class AnswerInputItemSerializer(serializers.Serializer):
    activity_id = serializers.IntegerField()
    input_data = serializers.DictField()

    def validate(self, attrs):
        attempt: ExamAttempt = self.context["attempt"]
        activity_id = attrs["activity_id"]
        input_data: Dict[str, Any] = attrs["input_data"]

        if not attempt.exam.activities.filter(id=activity_id).exists():
            raise serializers.ValidationError({
                "activity_id": f"Activity {activity_id} doesn't belong to this exam."
            })

        activity = Activity.objects.only("id", "type").get(pk=activity_id)
        in_serializer_class = ValidationStrategyRegistry.get_serializer(activity.type)
        if in_serializer_class is None:
            raise serializers.ValidationError({
                "activity_id": f"No serializer for activity type '{activity.type}'"
            })

        in_ser = in_serializer_class(data=input_data)
        in_ser.is_valid(raise_exception=True)

        attrs["input_data"] = in_ser.validated_data
        return attrs


class FinishAttemptRequestSerializer(serializers.Serializer):
    answers = serializers.ListField(
        child=AnswerInputItemSerializer(), allow_empty=False
    )

    def validate(self, attrs):
        activity_ids = [item["activity_id"] for item in attrs["answers"]]
        if len(activity_ids) != len(set(activity_ids)):
            raise serializers.ValidationError("Duplicated activity_id in answers.")
        return attrs

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        attempt: ExamAttempt = self.context["attempt"]
        fixed_answers: List[dict] = []
        for raw in data.get("answers", []):
            item_ser = AnswerInputItemSerializer(data=raw, context={"attempt": attempt})
            item_ser.is_valid(raise_exception=True)
            fixed_answers.append(item_ser.validated_data)
        ret["answers"] = fixed_answers
        return ret


class FinishAttemptResponseSerializer(serializers.ModelSerializer):
    attempt_id = serializers.IntegerField(source="id", read_only=True)
    percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = ExamAttempt
        fields = (
            "attempt_id",
            "exam_id",
            "status",
            "score_points",
            "max_points",
            "percentage",
            "passed",
            "correct_count",
            "total_questions",
            "finished_at",
        )


class StartAttemptResponseSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()
    attempt_number = serializers.IntegerField()
    time_limit_minutes = serializers.IntegerField(allow_null=True)
    status = serializers.CharField()
    started_at = serializers.DateTimeField()


class ExamAttemptStartSerializer(serializers.ModelSerializer):
    attempt_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = ExamAttempt
        fields = (
            "attempt_id",
            "attempt_number",
            "time_limit_minutes",
            "status",
            "started_at",
        )
        read_only_fields = fields


class VocabularySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vocabulary
        fields = ("id", "word", "meaning", "difficulty")


class ModuleProgressSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    total = serializers.IntegerField()
    completed = serializers.IntegerField()
    remaining = serializers.IntegerField()
    percent = serializers.FloatField()


class OverallProgressSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    completed = serializers.IntegerField()
    remaining = serializers.IntegerField()
    percent = serializers.FloatField()


class CourseProgressSerializer(serializers.Serializer):
    course = serializers.DictField()
    overall = OverallProgressSerializer()
    modules = ModuleProgressSerializer(many=True)
