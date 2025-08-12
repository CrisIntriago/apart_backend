from django import forms
from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from content.models import Module as ContentModule
from utils.enums import ActivityType

from .models.base import Activity
from .models.choice import Choice, ChoiceActivity
from .models.fill_in_the_blank import FillInTheBlankActivity
from .models.matching import MatchingActivity, MatchingPair
from .models.word_ordering import WordOrderingActivity


class ModuleLockedWidget(forms.HiddenInput):
    pass


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
class ChoiceActivityAdmin(ModulePresetMixin, ModelAdmin):
    list_display = ("title", "is_multiple", "difficulty", "created_at")
    search_fields = ("title",)
    list_filter = ("is_multiple", "difficulty")
    inlines = [ChoiceInline]
    ordering = ("-created_at",)

    def get_changeform_initial_data(self, request):
        return {"type": ActivityType.CHOICE}


@admin.register(FillInTheBlankActivity)
class FillInTheBlankActivityAdmin(ModulePresetMixin, ModelAdmin):
    list_display = ("title", "short_text", "difficulty", "created_at")
    search_fields = ("title", "text")
    ordering = ("-created_at",)

    def get_changeform_initial_data(self, request):
        return {"type": ActivityType.FILL}

    def short_text(self, obj):
        return (obj.text[:75] + "...") if len(obj.text) > 75 else obj.text

    short_text.short_description = "Texto"


class MatchingPairInline(ModulePresetMixin, TabularInline):
    model = MatchingPair
    extra = 2
    min_num = 1
    fields = ("left", "right")
    show_change_link = True


@admin.register(MatchingActivity)
class MatchingActivityAdmin(ModulePresetMixin, ModelAdmin):
    list_display = ("title", "difficulty", "created_at")
    search_fields = ("title",)
    ordering = ("-created_at",)
    inlines = [MatchingPairInline]

    def get_changeform_initial_data(self, request):
        return {"type": ActivityType.MATCH}


@admin.register(WordOrderingActivity)
class WordOrderingActivityAdmin(ModulePresetMixin, ModelAdmin):
    list_display = ("title", "short_sentence", "difficulty", "created_at")
    search_fields = ("title", "sentence")
    ordering = ("-created_at",)

    def short_sentence(self, obj):
        return (obj.sentence[:75] + "...") if len(obj.sentence) > 75 else obj.sentence

    def get_changeform_initial_data(self, request):
        return {"type": ActivityType.ORDER}

    short_sentence.short_description = "Oración"
