from django.contrib import admin

from .forms import PersonAdminForm
from .models import Person, Student, StudentLanguageProficiency


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    form = PersonAdminForm
    list_display = ("first_name", "last_name", "user")
    readonly_fields = ("user",)
    search_fields = ("first_name", "last_name", "national_id", "user__email")
    list_filter = ("country",)
    raw_id_fields = ("user",)


class StudentLanguageProficiencyInline(admin.TabularInline):
    model = StudentLanguageProficiency
    extra = 1
    min_num = 0
    fields = ("language", "level")
    autocomplete_fields = ("language",)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("person",)
    search_fields = ("person__first_name", "person__last_name")
    raw_id_fields = ("person",)
    inlines = [StudentLanguageProficiencyInline]
