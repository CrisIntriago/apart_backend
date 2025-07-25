from django.contrib.auth import authenticate
from rest_framework import serializers

from users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField() 
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data["email"], password=data["password"])
        if user and user.is_active:
            return {"user": user}
        raise serializers.ValidationError("Invalid credentials")
