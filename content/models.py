from django.db import models

from people.models import Student


class Vocabulary(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='vocabularies'
    )
    word = models.CharField(max_length=100)
    meaning = models.TextField()
    learned = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Vocabulary'
        verbose_name_plural = 'Vocabularies'
        db_table = 'vocabulary'

    def __str__(self):
        return f'{self.word} - {self.student}'
