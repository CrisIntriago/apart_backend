from knox.models import AuthToken

from users.models import User


def register_user(validated_data):
    user = User.objects.create_user(
        username=validated_data["username"],
        email=validated_data.get("email"),
        phone=validated_data.get("phone"),
        password=validated_data["password"],
    )
    return user


def register_token(user):
    return AuthToken.objects.create(user)[1]


def login_user(user):
    return AuthToken.objects.create(user)[1]
