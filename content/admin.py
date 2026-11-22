from django.contrib import admin

from .models import ChangeSet, ContentRevision, ContentSnapshot, SiteContent


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SiteContent)
class SiteContentAdmin(admin.ModelAdmin):
    list_display = ("key", "description", "updated_by", "updated_at")
    search_fields = ("key", "description")
    list_filter = ("updated_by",)
    readonly_fields = ("created_at", "updated_at")


class ContentRevisionInline(admin.TabularInline):
    model = ContentRevision
    extra = 0
    can_delete = False
    fields = ("key", "action", "version", "created_at")
    readonly_fields = fields
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ChangeSet)
class ChangeSetAdmin(ReadOnlyAdmin):
    list_display = ("id", "action", "actor", "created_count", "updated_count", "deleted_count", "created_at")
    list_filter = ("action", "actor")
    search_fields = ("note", "actor__email")
    readonly_fields = [f.name for f in ChangeSet._meta.fields]
    inlines = [ContentRevisionInline]


@admin.register(ContentRevision)
class ContentRevisionAdmin(ReadOnlyAdmin):
    list_display = ("id", "key", "action", "version", "actor", "changeset", "created_at")
    list_filter = ("action", "actor")
    search_fields = ("key",)
    readonly_fields = [f.name for f in ContentRevision._meta.fields]


@admin.register(ContentSnapshot)
class ContentSnapshotAdmin(ReadOnlyAdmin):
    list_display = ("id", "name", "key_count", "created_by", "created_at")
    list_filter = ("created_by",)
    search_fields = ("name", "note")
    readonly_fields = [f.name for f in ContentSnapshot._meta.fields]
