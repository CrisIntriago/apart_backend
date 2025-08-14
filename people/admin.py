from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .forms import PersonAdminForm
from .models import Enrollment, Person, Student, StudentLanguageProficiency


@admin.register(Person)
class PersonAdmin(ModelAdmin):
    form = PersonAdminForm
    list_display = ("first_name", "last_name", "user", "country")
    readonly_fields = ("user",)
    search_fields = (
        "first_name",
        "last_name",
        "user__email",
        "user__username",
    )
    list_filter = ("country",)
    raw_id_fields = ("user",)


class StudentLanguageProficiencyInline(TabularInline):
    model = StudentLanguageProficiency
    extra = 1
    min_num = 0
    fields = ("language", "level")
    autocomplete_fields = ("language",)


class EnrollmentInline(TabularInline):
    model = Enrollment
    extra = 1
    autocomplete_fields = ("course",)
    fields = (
        "course",
        "status",
        "start_at",
        "end_at",
    )
    readonly_fields = ()
    show_change_link = True


@admin.register(Student)
class StudentAdmin(ModelAdmin):
    list_display = ("person", "enrollments_count", "active_courses_display")
    search_fields = ("person__first_name", "person__last_name", "person__user__email")
    raw_id_fields = ("person",)
    inlines = [StudentLanguageProficiencyInline, EnrollmentInline]
    list_select_related = ("person",)

    def enrollments_count(self, obj):
        return obj.enrollments.count()

    enrollments_count.short_description = "Enrollments"

    def active_courses_display(self, obj):
        active = [
            e.course.name
            for e in obj.enrollments.select_related("course")
            if e.course and e.is_active_now()
        ]
        return ", ".join(active) if active else "—"

    active_courses_display.short_description = "Cursos activos"


@admin.register(Enrollment)
class EnrollmentAdmin(ModelAdmin):
    list_display = (
        "student",
        "course",
        "status",
        "start_at",
        "end_at",
        "progress_percent",
    )
    list_filter = ("status",)
    search_fields = (
        "student__person__first_name",
        "student__person__last_name",
        "course__name",
    )
    raw_id_fields = ("student", "course")
    autocomplete_fields = ("student", "course")
    list_select_related = ("student__person", "course")
    date_hierarchy = "start_at"
