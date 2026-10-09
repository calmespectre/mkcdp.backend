from django.contrib import admin
from .models import SiteContent, ContentRevision

@admin.register(SiteContent)
class SiteContentAdmin(admin.ModelAdmin):
    list_display = ("key", "description", "updated_by", "updated_at")
    search_fields = ("key", "description")
    readonly_fields = ("updated_at", "created_at")

@admin.register(ContentRevision)
class ContentRevisionAdmin(admin.ModelAdmin):
    list_display = ("key", "actor", "created_at")
    list_filter = ("key",)
    search_fields = ("key",)
    readonly_fields = ("key", "before", "after", "actor", "created_at")