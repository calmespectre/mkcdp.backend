from rest_framework import serializers

from .models import ChangeSet, ContentRevision, ContentSnapshot, SiteContent


def _email(user):
    return user.email if user else None


class SiteContentSerializer(serializers.ModelSerializer):
    updated_by_email = serializers.SerializerMethodField()

    class Meta:
        model = SiteContent
        fields = ("id", "key", "value", "description", "updated_by_email", "created_at", "updated_at")
        read_only_fields = fields

    def get_updated_by_email(self, obj):
        return _email(obj.updated_by)


class ContentRevisionSerializer(serializers.ModelSerializer):
    actor_email = serializers.SerializerMethodField()

    class Meta:
        model = ContentRevision
        fields = (
            "id",
            "changeset",
            "key",
            "action",
            "version",
            "before",
            "after",
            "actor",
            "actor_email",
            "created_at",
        )
        read_only_fields = fields

    def get_actor_email(self, obj):
        return _email(obj.actor)


class ChangeSetSerializer(serializers.ModelSerializer):
    actor_email = serializers.SerializerMethodField()
    total_changes = serializers.SerializerMethodField()

    class Meta:
        model = ChangeSet
        fields = (
            "id",
            "action",
            "note",
            "actor",
            "actor_email",
            "created_count",
            "updated_count",
            "deleted_count",
            "total_changes",
            "source_changeset",
            "source_revision",
            "source_snapshot",
            "created_at",
        )
        read_only_fields = fields

    def get_actor_email(self, obj):
        return _email(obj.actor)

    def get_total_changes(self, obj):
        return obj.created_count + obj.updated_count + obj.deleted_count


class ChangeSetDetailSerializer(ChangeSetSerializer):
    revisions = ContentRevisionSerializer(many=True, read_only=True)

    class Meta(ChangeSetSerializer.Meta):
        fields = ChangeSetSerializer.Meta.fields + ("revisions",)
        read_only_fields = fields


class ContentSnapshotSerializer(serializers.ModelSerializer):
    created_by_email = serializers.SerializerMethodField()

    class Meta:
        model = ContentSnapshot
        fields = ("id", "name", "note", "key_count", "created_by", "created_by_email", "created_at")
        read_only_fields = fields

    def get_created_by_email(self, obj):
        return _email(obj.created_by)


class ContentSnapshotDetailSerializer(ContentSnapshotSerializer):
    class Meta(ContentSnapshotSerializer.Meta):
        fields = ContentSnapshotSerializer.Meta.fields + ("data",)
        read_only_fields = fields
