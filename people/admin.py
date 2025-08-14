from django.contrib import admin, messages
from django.db import IntegrityError, transaction
from django.forms.utils import ErrorList
from unfold.admin import ModelAdmin, TabularInline

from utils.enums import EnrollmentStatus

from .forms import PersonAdminForm, StudentAdminForm
from .models import (
    Enrollment,
    Person,
    Student,
    StudentLanguageProficiency,
)
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
        """
        Valida 'máximo 1 ACTIVA' sin crear FormSet custom.
        Si hay más de una, mostramos errores y NO guardamos ese formset,
        pero dejamos atributos internos para que el admin no falle.
        """
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
