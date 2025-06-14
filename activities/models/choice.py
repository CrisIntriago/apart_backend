from django.db import models

from .base import BaseActivity


class ChoiceActivity(BaseActivity):
    is_multiple = models.BooleanField(
        default=False,
        help_text="Marcar True si permite seleccionar múltiples opciones",
    )

    class Meta:
        db_table = "choice_activity"


class Choice(models.Model):
    activity = models.ForeignKey(
        ChoiceActivity,
        related_name="choices",
        on_delete=models.CASCADE,
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    class Meta:
        db_table = "choice"
