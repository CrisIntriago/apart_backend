from django.db import models

from activities.models.base import BaseActivity


class WordOrderingActivity(BaseActivity):
    sentence = models.TextField(
        help_text="Oración correcta, p.ej. 'El gato está durmiendo'"
    )

    class Meta:
        db_table = "word_ordering_activity"
