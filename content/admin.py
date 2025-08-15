from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin, TabularInline

from activities.models.base import Activity, ActivityType, ExamActivity
from activities.models.choice import ChoiceActivity
from activities.models.fill_in_the_blank import FillInTheBlankActivity
from activities.models.matching import MatchingActivity
from activities.models.word_ordering import WordOrderingActivity

from .models import Course, Exam, Module


class ReadonlyActivityInlineBase(TabularInline):
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ("title", "difficulty", "created_at")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by("-created_at")


class ChoiceActivityInline(ReadonlyActivityInlineBase):
    model = ChoiceActivity


class FillInTheBlankActivityInline(ReadonlyActivityInlineBase):
    model = FillInTheBlankActivity


class MatchingActivityInline(ReadonlyActivityInlineBase):
    model = MatchingActivity


class WordOrderingActivityInline(ReadonlyActivityInlineBase):
    model = WordOrderingActivity


@admin.register(Module)
class ModuleAdmin(ModelAdmin):
    class Media:
        css = {"all": ("admin/custom/buttons.css",)}

    list_display = ("name", "course", "end_date", "activities_count")
    fields = (
        "course",
        "name",
        "description",
        "image",
        "difficulty",
        "end_date",
        "add_activities",
    )
    readonly_fields = ("add_activities",)
    inlines = [
        ChoiceActivityInline,
        FillInTheBlankActivityInline,
        MatchingActivityInline,
        WordOrderingActivityInline,
    ]

    def activities_count(self, obj):
        return Activity.objects.filter(module=obj).count()

    activities_count.short_description = "Actividades"

    def add_activities(self, obj):
        if not obj or not obj.pk:
            return "Guarda el módulo para ver opciones de creación."

        links = [
            (
                "+ Opción múltiple",
                reverse("admin:activities_choiceactivity_add") + f"?module={obj.pk}",
            ),
            (
                "+ Completar espacios",
                reverse("admin:activities_fillintheblankactivity_add")
                + f"?module={obj.pk}",
            ),
            (
                "+ Emparejamiento",
                reverse("admin:activities_matchingactivity_add") + f"?module={obj.pk}",
            ),
            (
                "+ Ordenar palabras",
                reverse("admin:activities_wordorderingactivity_add")
                + f"?module={obj.pk}",
            ),
        ]

        buttons = format_html_join(
            "",
            '<a href="{}" class="apart-btn apart-btn--primary">{}</a>',
            ((url, label) for label, url in links),
        )

        return format_html(buttons)

    add_activities.short_description = "Crear nuevas actividades"


class ModuleInline(TabularInline):
    model = Module
    extra = 1
    show_change_link = True


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)
    inlines = [ModuleInline]


class BaseExamActivityROInline(TabularInline):
    model = ExamActivity
    extra = 0
    can_delete = False
    fields = ("activity_link", "required")
    readonly_fields = fields
    activity_type = None

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.activity_type is None:
            return qs.none()
        return qs.select_related("activity").filter(activity__type=self.activity_type)

    def activity_link(self, obj):
        url = reverse("admin:activities_activity_change", args=[obj.activity_id])
        return mark_safe(f'<a class="button" href="{url}">{obj.activity.title}</a>')

    activity_link.short_description = "Actividad"


class ExamChoiceInline(BaseExamActivityROInline):
    verbose_name_plural = "Opción múltiple"
    activity_type = ActivityType.CHOICE


class ExamFillInTheBlankInline(BaseExamActivityROInline):
    verbose_name_plural = "Completar espacios"
    activity_type = ActivityType.FILL


class ExamMatchingInline(BaseExamActivityROInline):
    verbose_name_plural = "Emparejamiento"
    activity_type = ActivityType.MATCH


class ExamWordOrderingInline(BaseExamActivityROInline):
    verbose_name_plural = "Ordenar palabras"
    activity_type = ActivityType.ORDER


class ExamActivityInline(TabularInline):
    model = ExamActivity
    extra = 0
    fields = ("activity", "required")
    autocomplete_fields = ("activity",)


@admin.register(Exam)
class ExamAdmin(ModelAdmin):
    class Media:
        css = {"all": ("admin/custom/buttons.css",)}

    list_display = ("__str__", "course", "type", "is_published", "items_count")
    fields = (
        "course",
        "type",
        "title",
        "description",
        "is_published",
        "time_limit_minutes",
        "attempts_allowed",
        "add_activities",
    )
    readonly_fields = ("add_activities",)

    inlines = [
        ExamChoiceInline,
        ExamFillInTheBlankInline,
        ExamMatchingInline,
        ExamWordOrderingInline,
        ExamActivityInline,
    ]

    def items_count(self, obj):
        return obj.activities.count()

    items_count.short_description = "Actividades"

    def add_activities(self, obj):
        if not obj or not obj.pk:
            return "Guarda el examen para ver opciones de creación."
        links = [
            (
                "+ Opción múltiple",
                reverse("admin:activities_choiceactivity_add") + f"?exam={obj.pk}",
            ),
            (
                "+ Completar espacios",
                reverse("admin:activities_fillintheblankactivity_add")
                + f"?exam={obj.pk}",
            ),
            (
                "+ Emparejamiento",
                reverse("admin:activities_matchingactivity_add") + f"?exam={obj.pk}",
            ),
            (
                "+ Ordenar palabras",
                reverse("admin:activities_wordorderingactivity_add")
                + f"?exam={obj.pk}",
            ),
        ]
        buttons = format_html_join(
            "",
            '<a href="{}" class="apart-btn apart-btn--primary">{}</a>',
            ((url, label) for label, url in links),
        )
        return format_html(buttons)

    add_activities.short_description = "Crear y asociar actividades"
