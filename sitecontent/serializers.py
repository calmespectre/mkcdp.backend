from rest_framework import serializers

from .models import SiteContentEdit, SiteContentVersion


class SiteContentEditSerializer(serializers.ModelSerializer):
    updated_by_email = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SiteContentEdit
        fields = ["id", "key", "value", "updated_by", "updated_by_email", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at", "updated_by", "updated_by_email"]

    def get_updated_by_email(self, obj):
        return obj.updated_by.email if obj.updated_by else None


class SiteContentVersionSerializer(serializers.ModelSerializer):
    created_by_email = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SiteContentVersion
        fields = ["id", "snapshot", "created_by", "created_by_email", "note", "created_at"]
        read_only_fields = ["id", "created_at", "created_by", "created_by_email"]

    def get_created_by_email(self, obj):
        return obj.created_by.email if obj.created_by else None