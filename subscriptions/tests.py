from django.test import TestCase
from subscriptions.models import Subscription, PlanChoices
from people.models import Student, Person
from users.models import User
from datetime import date

class SubscriptionModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='testpass'
        )
        self.person = Person.objects.create(user=self.user, date_of_birth=date(2000, 1, 1))
        self.student = Student.objects.create(person=self.person)

    def test_create_subscription(self):
        sub = Subscription.objects.create(student=self.student, plan=PlanChoices.MONTHLY)
        self.assertEqual(sub.student, self.student)
        self.assertEqual(sub.plan, PlanChoices.MONTHLY)

    def test_str_representation(self):
        sub = Subscription.objects.create(student=self.student, plan=PlanChoices.ANNUAL)
        self.assertIn('annual', str(sub))

    def test_unique_subscription_per_student(self):
        Subscription.objects.create(student=self.student, plan=PlanChoices.MONTHLY)
        with self.assertRaises(Exception):
            Subscription.objects.create(student=self.student, plan=PlanChoices.ANNUAL)