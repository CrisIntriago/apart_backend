from django.db import models

from activities.models.base import BaseActivity


class FillInTheBlankActivity(BaseActivity):
    text = models.TextField(
        help_text="Texto con marcadores de posición, p.ej. 'La capital de Francia es {{blank}}'"  # noqa: E501
    )
    correct_answers = models.JSONField(
        help_text="Diccionario de índices y respuestas correctas, p.ej. {'0': 'París'}"
    )

    class Meta:
        db_table = "fill_in_the_blank_activity"
