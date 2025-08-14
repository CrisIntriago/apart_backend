# admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
)

from .models import PlanChoices, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = (
        "id",
        "student_link",
        "plan_badge",
        "start_date",
        "end_date",
        "active_badge",
    )
    list_select_related = ("student__person",)

    search_fields = (
        "student__person__first_name",
        "student__person__last_name",
        "student__person__user__email",
    )

    list_filter = (
        ("student", AutocompleteSelectFilter),
        "plan",
        "is_active",
    )

    date_hierarchy = "start_date"
    ordering = ("-start_date",)
    autocomplete_fields = ("student",)

    @admin.display(description="Estudiante", ordering="student__person__first_name")
    def student_link(self, obj: Subscription):
        url = reverse("admin:people_student_change", args=[obj.student_id])
        person = getattr(obj.student, "person", None)
        name = (
            f"{person.first_name} {person.last_name}"
            if person
            else f"ID {obj.student_id}"
        )
        return format_html('<a href="{}">{}</a>', url, name)

    @admin.display(description="Plan")
    def plan_badge(self, obj: Subscription):
        color = {
            PlanChoices.MONTHLY: "#2563eb",
            PlanChoices.ANNUAL: "#16a34a",
        }.get(obj.plan, "#374151")
        return format_html(
            '<span style="padding:2px 8px;border-radius:999px;'
            'background:{};color:white;font-size:12px;">{}</span>',
            color,
            obj.get_plan_display(),
        )

    @admin.display(description="Estado")
    def active_badge(self, obj: Subscription):
        color = "#16a34a" if obj.is_active else "#dc2626"
        label = "Activa" if obj.is_active else "Inactiva"
        return format_html(
            '<span style="padding:2px 8px;border-radius:999px;'
            'background:{};color:white;font-size:12px;">{}</span>',
            color,
            label,
        )

    @admin.action(description="Marcar como activa")
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Marcar como inactiva")
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Cambiar plan a Mensual")
    def set_monthly(self, request, queryset):
        queryset.update(plan=PlanChoices.MONTHLY)

    @admin.action(description="Cambiar plan a Anual")
    def set_annual(self, request, queryset):
        queryset.update(plan=PlanChoices.ANNUAL)

    actions = ["mark_active", "mark_inactive", "set_monthly", "set_annual"]
