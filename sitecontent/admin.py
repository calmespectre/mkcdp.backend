from django.contrib import admin

from .models import SiteContentEdit, SiteContentVersion


@admin.register(SiteContentEdit)
class SiteContentEditAdmin(admin.ModelAdmin):
    list_display = ("key", "updated_by", "updated_at")
    list_filter = ("updated_by",)
    search_fields = ("key",)
    ordering = ("key",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(SiteContentVersion)
class SiteContentVersionAdmin(admin.ModelAdmin):
    list_display = ("id", "note", "created_by", "created_at")
    list_filter = ("created_by",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)