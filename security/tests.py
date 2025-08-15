from django.test import TestCase
from rest_framework.test import APIClient

from users.models import User


class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/auth/register/"
        self.login_url = "/api/auth/login/"
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "phone": "0999999999",
            "password": "securepassword",
            "first_name": "Test",
            "last_name": "User",
            "country": "Ecuador",
            "date_of_birth": "2000-01-01",
            "languages": ["es", "en"],
        }

    def test_register_user(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, 201)

    def test_login_user(self):
        user = User.objects.create_user(
            username=self.user_data["username"],
            email=self.user_data["email"],
            phone=self.user_data["phone"],
            password=self.user_data["password"],
            first_name=self.user_data["first_name"],
            last_name=self.user_data["last_name"],
        )
        from people.models import Person
        Person.objects.create(
            user=user,
            first_name=self.user_data["first_name"],
            last_name=self.user_data["last_name"],
            date_of_birth=self.user_data["date_of_birth"],
            country=self.user_data["country"],
            languages=self.user_data["languages"],
        )

        login_payload = {
            "email": self.user_data["email"],
            "password": self.user_data["password"],
        }

        response = self.client.post(self.login_url, login_payload)
        self.assertEqual(response.status_code, 200)
