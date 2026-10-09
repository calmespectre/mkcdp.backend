from django.contrib import admin
from .models import SafeguardingReport, SafeguardingNote

@admin.register(SafeguardingReport)
class SafeguardingReportAdmin(admin.ModelAdmin):
    list_display = ("reference", "urgency", "status", "anonymous", "location", "created_at")
    list_filter = ("status", "urgency", "anonymous")
    search_fields = ("reference", "child_name", "location", "full_name")
    readonly_fields = ("id", "reference", "created_at", "updated_at")

@admin.register(SafeguardingNote)
class SafeguardingNoteAdmin(admin.ModelAdmin):
    list_display = ("report", "author", "created_at")
    search_fields = ("report__reference",)