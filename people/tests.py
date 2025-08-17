from django.test import TestCase
from rest_framework.test import APIClient
from people.models import Person, Student
from datetime import date
from users.models import User
from subscriptions.models import Subscription, PlanChoices

class UpdateAccessViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/people/update-access/'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepassword',
        )
        self.person = Person.objects.create(
            user=self.user,
            has_access=False,
            date_of_birth=date(2000, 1, 1)
        )
        self.student = Student.objects.create(person=self.person)

    def test_missing_email(self):
        data = {"hasAccess": True, "planType": PlanChoices.MONTHLY}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        resp_json = response.json()
        self.assertTrue('detail' in resp_json or 'email' in resp_json)

    def test_person_not_found(self):
        data = {"hasAccess": True, "email": "notfound@example.com", "planType": PlanChoices.MONTHLY}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('No existe un usuario con ese email.', response.json()['detail'])

    def test_update_access_and_create_subscription(self):
        data = {"hasAccess": True, "email": self.user.email, "planType": PlanChoices.MONTHLY}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.person.refresh_from_db()
        self.assertTrue(self.person.has_access)
        self.assertTrue(Subscription.objects.filter(student=self.student, plan=PlanChoices.MONTHLY).exists())

    def test_update_access_no_planType(self):
        data = {"hasAccess": True, "email": self.user.email}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        resp_json = response.json()
        self.assertTrue('planType' in resp_json or 'non_field_errors' in resp_json)

    def test_update_access_revoke(self):
        Subscription.objects.create(student=self.student, plan=PlanChoices.MONTHLY)
        self.person.has_access = True
        self.person.save()
        data = {"hasAccess": False, "email": self.user.email, "planType": PlanChoices.MONTHLY}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.person.refresh_from_db()
        self.assertFalse(self.person.has_access)
        self.assertTrue(Subscription.objects.filter(student=self.student).exists())