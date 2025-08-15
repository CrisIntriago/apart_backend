from django.db import models

from .base import Activity


class WordOrderingActivity(Activity):
    class Meta:
        db_table = "word_ordering_activity"
        verbose_name = "Word Ordering Activity"
        verbose_name_plural = "Word Ordering Activities"

    sentence = models.TextField(
        help_text="Oración correcta, p.ej. 'El gato está durmiendo'"
    )
