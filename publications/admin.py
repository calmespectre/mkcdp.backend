from django.contrib import admin

from .models import Publication


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "year", "published", "file_type", "file_size", "created_at")
    list_filter = ("category", "published", "year")
    search_fields = ("title", "description", "slug")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-year", "order", "-created_at")
    readonly_fields = ("file_size", "file_type", "created_at", "updated_at")