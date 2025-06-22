from django.contrib import admin

from languages.models import Language


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    search_fields = ("name",)
