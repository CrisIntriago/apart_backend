from django.db import models

from .base import Activity


class MatchingActivity(Activity):
    pass

    class Meta:
        db_table = "matching_activity"


class MatchingPair(models.Model):
    class Meta:
        db_table = "matching_pair"

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
