from django.db import models


class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)
    icon = models.ImageField(
        upload_to="languages/icons/",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Language"
        verbose_name_plural = "Languages"
        db_table = "languages"

    def __str__(self):
        return self.name
