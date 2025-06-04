from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
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
        }

    def test_register_user(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, 201)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["username"], self.user_data["username"])

    def test_login_user(self):
        User.objects.create_user(
            username=self.user_data["username"],
            email=self.user_data["email"],
            phone=self.user_data["phone"],
            password=self.user_data["password"],
        )

        login_payload = {
            "username": self.user_data["username"],
            "password": self.user_data["password"],
        }

        response = self.client.post(self.login_url, login_payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
