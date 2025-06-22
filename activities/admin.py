from django.contrib import admin

from utils.enums import ActivityType

from .models.base import Activity
from .models.choice import Choice, ChoiceActivity
from .models.fill_in_the_blank import FillInTheBlankActivity
from .models.matching import MatchingActivity, MatchingPair
from .models.word_ordering import WordOrderingActivity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "difficulty", "created_at")
    search_fields = ("title", "description")
    list_filter = ("type", "difficulty")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2
    min_num = 1
    max_num = 10
    fields = ("text", "is_correct")
    show_change_link = True


@admin.register(ChoiceActivity)
class ChoiceActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "is_multiple", "difficulty", "created_at")
    search_fields = ("title",)
    list_filter = ("is_multiple", "difficulty")
    inlines = [ChoiceInline]
    ordering = ("-created_at",)

    def get_changeform_initial_data(self, request):
        return {"type": ActivityType.CHOICE}


@admin.register(FillInTheBlankActivity)
class FillInTheBlankActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "short_text", "difficulty", "created_at")
    search_fields = ("title", "text")
    ordering = ("-created_at",)

    def get_changeform_initial_data(self, request):
        return {"type": ActivityType.FILL}

    def short_text(self, obj):
        return (obj.text[:75] + "...") if len(obj.text) > 75 else obj.text

    short_text.short_description = "Texto"


class MatchingPairInline(admin.TabularInline):
    model = MatchingPair
    extra = 2
    min_num = 1
    fields = ("left", "right")
    show_change_link = True


@admin.register(MatchingActivity)
class MatchingActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "difficulty", "created_at")
    search_fields = ("title",)
    ordering = ("-created_at",)
    inlines = [MatchingPairInline]

    def get_changeform_initial_data(self, request):
        return {"type": ActivityType.MATCH}


@admin.register(WordOrderingActivity)
class WordOrderingActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "short_sentence", "difficulty", "created_at")
    search_fields = ("title", "sentence")
    ordering = ("-created_at",)

    def short_sentence(self, obj):
        return (obj.sentence[:75] + "...") if len(obj.sentence) > 75 else obj.sentence

    def get_changeform_initial_data(self, request):
        return {"type": ActivityType.ORDER}

    short_sentence.short_description = "Oración"
