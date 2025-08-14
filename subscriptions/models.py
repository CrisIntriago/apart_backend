from django.db import models

from people.models import Student


class PlanChoices(models.TextChoices):
    MONTHLY = "monthly", "Mensual"
    ANNUAL = "annual", "Anual"


class Subscription(models.Model):
    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        db_table = "subscriptions"

    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.CharField(
        max_length=20, choices=PlanChoices.choices, default=PlanChoices.MONTHLY
    )
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student} - {self.plan}"
