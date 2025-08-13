from django.contrib.auth import authenticate
from rest_framework import serializers

from users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    google_token = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "google_token"]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    google_token = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data.get("google_token"):
            return data
        user = authenticate(username=data.get("username"), password=data.get("password"))
        if user and user.is_active:
            return {"user": user}
        raise serializers.ValidationError("Invalid credentials")
