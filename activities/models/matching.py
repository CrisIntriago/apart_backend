from django.db import models

from activities.models.base import BaseActivity


class MatchingActivity(BaseActivity):
    pass

    class Meta:
        db_table = "matching_activity"


class MatchingPair(models.Model):
    activity = models.ForeignKey(
        MatchingActivity,
        related_name="pairs",
        on_delete=models.CASCADE,
    )
    left = models.CharField(max_length=255)
    right = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.left} ↔ {self.right}"

    class Meta:
        db_table = "matching_pair"
