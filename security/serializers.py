from django.contrib.auth import authenticate
from rest_framework import serializers

from users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    country = serializers.CharField(write_only=True)
    date_of_birth = serializers.DateField(write_only=True)
    languages = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=0,
        max_length=3,
        write_only=True,
    )
    photo = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "country",
            "date_of_birth",
            "languages",
            "photo",
        ]


class EmailValidationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data["email"], password=data["password"])
        if user and user.is_active:
            return {"user": user}
        raise serializers.ValidationError("Invalid credentials")


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginGoogleSerializer(serializers.Serializer):
    google_token = serializers.CharField()

    def validate(self, data):
        user = authenticate(google_token=data["google_token"])
        if user and user.is_active:
            return {"user": user}
        raise serializers.ValidationError("Invalid credentials")


class RegisterGoogleSerializer(serializers.Serializer):
    google_token = serializers.CharField()

    def validate(self, data):
        user = authenticate(google_token=data["google_token"])
        if user and user.is_active:
            return {"user": user}
        raise serializers.ValidationError("Invalid credentials")
