from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from activities.models.base import ExamActivity
from content.models import Exam
from content.models import Module as ContentModule
from utils.enums import ActivityType

from .forms import FillInTheBlankActivityForm
from .models.base import Activity
from .models.choice import Choice, ChoiceActivity
from .models.fill_in_the_blank import FillInTheBlankActivity
from .models.matching import MatchingActivity, MatchingPair
from .models.word_ordering import WordOrderingActivity


class ModuleLockedWidget(forms.HiddenInput):
    pass


class TypeLockedMixin:
    ACTIVITY_TYPE = None

    def get_changeform_initial_data(self, request):
        data = super().get_changeform_initial_data(request)
        data = dict(data or {})
        if self.ACTIVITY_TYPE is not None:
            data["type"] = self.ACTIVITY_TYPE
        return data

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "type" in form.base_fields:
            form.base_fields["type"].initial = self.ACTIVITY_TYPE
            form.base_fields["type"].disabled = True
            form.base_fields["type"].widget = forms.HiddenInput()
        return form

    def save_model(self, request, obj, form, change):
        if self.ACTIVITY_TYPE is not None:
            obj.type = self.ACTIVITY_TYPE
        super().save_model(request, obj, form, change)


class ModulePresetMixin:
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "module":
            module_id = request.GET.get("module") or request.POST.get("module")
            if module_id:
                kwargs["initial"] = module_id
                kwargs["queryset"] = ContentModule.objects.filter(pk=module_id)
            else:
                kwargs["queryset"] = ContentModule.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        module_id = request.GET.get("module") or request.POST.get("module")
        if module_id and "module" in form.base_fields and obj is None:
            form.base_fields["module"].widget = ModuleLockedWidget()
        return form


def _admin_change_url_for(model_class, pk):
    return reverse(
        f"admin:{model_class._meta.app_label}_{model_class._meta.model_name}_change",
        args=[pk],
    )


class AttachToExamOnCreateMixin:
    def _maybe_attach_and_redirect(self, request, obj, default_response):
        exam_id = request.GET.get("exam") or request.POST.get("exam")
        if not exam_id:
            return default_response

        created = False
        try:
            _, created = ExamActivity.objects.get_or_create(
                exam_id=exam_id, activity_id=obj.pk
            )
        except Exception as exc:
            messages.warning(
                request,
                f"No se pudo vincular la actividad al examen {exam_id}: {exc}",
            )
            return default_response

        if created:
            messages.success(request, f"Actividad vinculada al examen #{exam_id}.")

        if "_continue" in request.POST or "_addanother" in request.POST:
            return default_response

        try:
            exam_change_url = _admin_change_url_for(Exam, exam_id)
            return HttpResponseRedirect(exam_change_url)
        except Exception:
            return default_response

    def response_add(self, request, obj, post_url_continue=None):
        resp = super().response_add(request, obj, post_url_continue)
        return self._maybe_attach_and_redirect(request, obj, resp)

    def response_change(self, request, obj):
        resp = super().response_change(request, obj)
        return self._maybe_attach_and_redirect(request, obj, resp)


@admin.register(Activity)
class ActivityAdmin(ModelAdmin):
    list_display = ("title", "type", "difficulty", "created_at")
    search_fields = ("title", "description")
    list_filter = ("type", "difficulty")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request)


class ChoiceInline(TabularInline):
    model = Choice
    extra = 2
    min_num = 1
    max_num = 10
    fields = ("text", "is_correct")
    show_change_link = True


@admin.register(ChoiceActivity)
class ChoiceActivityAdmin(
    TypeLockedMixin, AttachToExamOnCreateMixin, ModulePresetMixin, ModelAdmin
):
    ACTIVITY_TYPE = ActivityType.CHOICE
    exclude = ("type",)
    list_display = ("title", "is_multiple", "difficulty", "created_at")
    search_fields = ("title",)
    list_filter = ("is_multiple", "difficulty")
    inlines = [ChoiceInline]
    ordering = ("-created_at",)

    def get_changeform_initial_data(self, request):
        return {"type": ActivityType.CHOICE}


@admin.register(FillInTheBlankActivity)
class FillInTheBlankActivityAdmin(
    TypeLockedMixin, AttachToExamOnCreateMixin, ModulePresetMixin, ModelAdmin
):
    form = FillInTheBlankActivityForm
    ACTIVITY_TYPE = ActivityType.FILL
    exclude = ("type",)

    list_display = ("title", "short_text", "difficulty", "created_at")
    search_fields = ("title", "text")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("title", "instructions", "difficulty", "points", "module")}),
        ("Contenido", {"fields": ("authoring_text",)}),
        ("Vista previa", {"fields": ("preview_text",)}),
    )
    readonly_fields = ("preview_text",)

    def get_changeform_initial_data(self, request):
        return {"type": ActivityType.FILL}

    def short_text(self, obj):
        return (
            (obj.text[:75] + "...")
            if obj.text and len(obj.text) > 75
            else (obj.text or "-")
        )

    short_text.short_description = "Texto"

    def preview_text(self, obj):
        if not obj or not getattr(obj, "text", None):
            return "-"
        return format_html(obj.text.replace("{{blank}}", "<strong>____</strong>"))

    preview_text.short_description = "Previsualización"


class MatchingPairInline(ModulePresetMixin, TabularInline):
    model = MatchingPair
    extra = 2
    min_num = 1
    fields = ("left", "right")
    show_change_link = True


@admin.register(MatchingActivity)
class MatchingActivityAdmin(
    TypeLockedMixin, AttachToExamOnCreateMixin, ModulePresetMixin, ModelAdmin
):
    ACTIVITY_TYPE = ActivityType.MATCH
    exclude = ("type",)

    list_display = ("title", "difficulty", "created_at")
    search_fields = ("title",)
    ordering = ("-created_at",)
    inlines = [MatchingPairInline]

    def get_changeform_initial_data(self, request):
        return {"type": ActivityType.MATCH}


@admin.register(WordOrderingActivity)
class WordOrderingActivityAdmin(
    TypeLockedMixin, AttachToExamOnCreateMixin, ModulePresetMixin, ModelAdmin
):
    ACTIVITY_TYPE = ActivityType.ORDER
    exclude = ("type",)

    list_display = ("title", "short_sentence", "difficulty", "created_at")
    search_fields = ("title", "sentence")
    ordering = ("-created_at",)

    def short_sentence(self, obj):
        return (obj.sentence[:75] + "...") if len(obj.sentence) > 75 else obj.sentence

    def get_changeform_initial_data(self, request):
        return {"type": ActivityType.ORDER}

    short_sentence.short_description = "Oración"
