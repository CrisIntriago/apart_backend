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

    class Meta:
        model = User
        fields = [
            "username", "email", "password", "first_name", "last_name",
            "country", "date_of_birth", "languages",
        ]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField() 
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data["email"], password=data["password"])
        if user and user.is_active:
            return {"user": user}
        raise serializers.ValidationError("Invalid credentials")
