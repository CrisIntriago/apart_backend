from dalf.admin import DALFModelAdmin, DALFRelatedFieldAjax
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.forms.utils import ErrorList
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from utils.enums import EnrollmentStatus

from .forms import PersonAdminForm, StudentAdminForm
from .models import Enrollment, Person, Student, StudentLanguageProficiency
from .utils import sync_active_course


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
    form = StudentAdminForm
    list_display = ("person", "enrollments_count", "active_course")
    search_fields = ("person__first_name", "person__last_name", "person__user__email")
    raw_id_fields = ("person",)
    inlines = [EnrollmentInline]
    list_select_related = ("person",)
    readonly_fields = ("active_course",)

    def enrollments_count(self, obj):
        return obj.enrollments.count()

    enrollments_count.short_description = "Enrollments"

    def save_formset(self, request, form, formset, change):
        if formset.model is Enrollment:
            active_count = 0
            for f in formset.forms:
                cd = getattr(f, "cleaned_data", None)
                if not cd or cd.get("DELETE"):
                    continue
                if cd.get("status") == EnrollmentStatus.ACTIVE:
                    active_count += 1

            if active_count > 1:
                formset._non_form_errors = ErrorList([
                    "Sólo puede haber una matrícula ACTIVA por estudiante."
                ])
                form.add_error(
                    None, "Sólo puede haber una matrícula ACTIVA por estudiante."
                )
                self.message_user(
                    request,
                    "Revisa las matrículas: sólo puede haber una ACTIVA por estudiante.",  # noqa: E501
                    level=messages.ERROR,
                )
                formset.new_objects = []
                formset.changed_objects = []
                formset.deleted_objects = []
                return

        return super().save_formset(request, form, formset, change)

    def save_related(self, request, form, formsets, change):
        try:
            with transaction.atomic():
                resp = super().save_related(request, form, formsets, change)

                student = form.instance
                if student and student.pk:
                    sync_active_course(student)

                return resp
        except IntegrityError:
            form.add_error(
                None,
                "No se pudo guardar porque se violó una restricción "
                "(unicidad o una sola matrícula ACTIVA).",
            )
            self.message_user(
                request,
                "No se pudo guardar: verifica ‘status’ y que no repitas (student, course).",  # noqa: E501
                level=messages.ERROR,
            )


class ActiveNowFilter(SimpleListFilter):
    title = _("Vigencia actual")
    parameter_name = "active_now"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Activas ahora")),
            ("no", _("No activas ahora")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        from django.utils import timezone

        now = timezone.now()
        active_q = (
            Q(status=EnrollmentStatus.ACTIVE)
            & (Q(start_at__isnull=True) | Q(start_at__lte=now))
            & (Q(end_at__isnull=True) | Q(end_at__gte=now))
        )
        if value == "yes":
            return queryset.filter(active_q)
        if value == "no":
            return queryset.exclude(active_q)
        return queryset


@admin.register(Enrollment)
class EnrollmentAdmin(DALFModelAdmin):  # 👈 usar DALFModelAdmin
    list_display = (
        "id",
        "student_link",
        "course_link",
        "status_badge",
        "enrolled_at",
        "start_at",
        "end_at",
        "progress_percent",
        "last_activity_at",
    )
    list_select_related = ("student__person", "course")
    search_fields = (
        "student__person__first_name",
        "student__person__last_name",
        "student__person__user__email",
        "course__name",
    )
    list_filter = (
        ActiveNowFilter,
        "status",
        ("student", DALFRelatedFieldAjax),
        ("course", DALFRelatedFieldAjax),
    )
    date_hierarchy = "enrolled_at"
    ordering = ("-enrolled_at",)
    autocomplete_fields = ("student", "course")
    actions = []

    @admin.display(description="Estudiante", ordering="student__person__first_name")
    def student_link(self, obj):
        url = reverse("admin:people_student_change", args=[obj.student_id])
        person = getattr(obj.student, "person", None)
        name = (
            f"{person.first_name} {person.last_name}"
            if person
            else f"ID {obj.student_id}"
        )
        return format_html('<a href="{}">{}</a>', url, name)

    @admin.display(description="Curso", ordering="course__name")
    def course_link(self, obj):
        try:
            url = reverse("admin:content_course_change", args=[obj.course_id])
        except Exception:
            url = "#"
        name = getattr(obj.course, "name", f"ID {obj.course_id}")
        return format_html('<a href="{}">{}</a>', url, name)

    @admin.display(description="Estado")
    def status_badge(self, obj):
        color = {
            EnrollmentStatus.ACTIVE: "#16a34a",
            EnrollmentStatus.PAUSED: "#ca8a04",
            EnrollmentStatus.COMPLETED: "#2563eb",
            EnrollmentStatus.CANCELED: "#dc2626",
        }.get(obj.status, "#374151")
        return format_html(
            '<span style="padding:2px 8px;border-radius:999px;background:{};color:white;font-size:12px;">{}</span>',  # noqa: E501
            color,
            obj.get_status_display(),
        )
