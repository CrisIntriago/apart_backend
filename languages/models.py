from django.db import models


class Language(models.Model):
    class Meta:
        verbose_name = "Language"
        verbose_name_plural = "Languages"
        db_table = "languages"

    name = models.CharField(max_length=50, unique=True)
    icon = models.ImageField(
        upload_to="languages/icons/",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name
