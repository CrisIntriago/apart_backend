from django.db import models

from .base import Activity


class ChoiceActivity(Activity):
    class Meta:
        db_table = "choice_activity"
        verbose_name = "Choice Activity"
        verbose_name_plural = "Choice Activities"

    is_multiple = models.BooleanField(
        default=False,
        help_text="Marcar True si permite seleccionar múltiples opciones",
    )


class Choice(models.Model):
    class Meta:
        db_table = "choice"
        verbose_name = "Choice"
        verbose_name_plural = "Choices"

    activity = models.ForeignKey(
        ChoiceActivity,
        related_name="choices",
        on_delete=models.CASCADE,
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text
