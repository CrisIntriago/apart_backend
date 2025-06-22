from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Course, Module


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    list_display = ("name",)
    inlines = [ModuleInline]


@admin.register(Module)
class ModuleAdmin(ModelAdmin):
    list_display = ("name", "course")
