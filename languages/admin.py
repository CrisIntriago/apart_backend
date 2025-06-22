from django.contrib import admin
from unfold.admin import ModelAdmin

from languages.models import Language


@admin.register(Language)
class LanguageAdmin(ModelAdmin):
    search_fields = ("name",)
