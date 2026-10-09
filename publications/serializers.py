from rest_framework import serializers
from .models import Publication


class PublicationSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    category_label = serializers.CharField(read_only=True)
    file_size_display = serializers.CharField(read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Publication
        fields = (
            "id",
            "title",
            "slug",
            "category",
            "category_label",
            "year",
            "description",
            "file",
            "file_url",
            "file_size",
            "file_size_display",
            "file_type",
            "published",
            "uploaded_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "file_size", "file_type", "created_at", "updated_at")
        extra_kwargs = {
            "file": {"write_only": True, "required": False},
            "title": {"required": True},
        }

    def get_file_url(self, obj):
        if not obj.file:
            return ""
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url

    def get_uploaded_by_name(self, obj):
        if not obj.uploaded_by:
            return ""
        return obj.uploaded_by.full_name or obj.uploaded_by.email