from django.db import models

from .base import Activity


class WordOrderingActivity(Activity):
    sentence = models.TextField(
        help_text="Oración correcta, p.ej. 'El gato está durmiendo'"
    )

    class Meta:
        db_table = "word_ordering_activity"
