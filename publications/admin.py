from django.contrib import admin
from .models import Publication


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "year", "file_type", "published", "created_at")
    list_filter = ("category", "year", "published", "file_type")
    search_fields = ("title", "description")
    readonly_fields = ("id", "slug", "file_size", "file_type", "created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("-year", "-created_at")