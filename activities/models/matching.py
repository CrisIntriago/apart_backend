from django.db import models

from .base import Activity


class MatchingActivity(Activity):
    pass

    class Meta:
        db_table = "matching_activity"
        verbose_name = "Matching Activity"
        verbose_name_plural = "Matching Activities"


class MatchingPair(models.Model):
    class Meta:
        db_table = "matching_pair"
        verbose_name = "Matching Pair"
        verbose_name_plural = "Matching Pairs"

    activity = models.ForeignKey(
        MatchingActivity,
        related_name="pairs",
        on_delete=models.CASCADE,
    )
    left = models.CharField(max_length=255)
    right = models.CharField(max_length=255)
    is_vocabulary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.left} - {self.right}"
