from knox.models import AuthToken

from users.models import User
from people.models import Person


def register_user(validated_data):
    user = User.objects.create_user(
        username=validated_data["username"],
        email=validated_data.get("email"),
        phone=validated_data.get("phone"),
        password=validated_data["password"],
    )
    
    Person.objects.create(
        user=user,
        first_name=validated_data["first_name"],
        last_name=validated_data["last_name"],
        date_of_birth=validated_data["date_of_birth"],
        country=validated_data["country"],
        languages=validated_data["languages"],
    )
    return user


def register_token(user):
    return AuthToken.objects.create(user)[1]


def login_user(user):
    return AuthToken.objects.create(user)[1]
