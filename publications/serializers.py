from rest_framework import serializers

from .models import Publication


class PublicationSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    category_label = serializers.SerializerMethodField()
    uploaded_by_email = serializers.SerializerMethodField()

    class Meta:
        model = Publication
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "category_label",
            "year",
            "description",
            "file",
            "file_url",
            "file_name",
            "file_size",
            "file_size_display",
            "file_type",
            "published",
            "order",
            "uploaded_by",
            "uploaded_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "file_size",
            "file_type",
            "uploaded_by",
            "uploaded_by_email",
            "created_at",
            "updated_at",
            "file_url",
            "file_name",
            "file_size_display",
            "category_label",
        ]
        extra_kwargs = {
            "file": {"required": True, "write_only": False},
        }

    def get_file_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get("request")
        try:
            url = obj.file.url
        except Exception:
            return None
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_file_name(self, obj):
        if not obj.file:
            return ""
        return obj.file.name.split("/")[-1]

    def get_file_size_display(self, obj):
        size = obj.file_size or 0
        if size <= 0:
            return ""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def get_category_label(self, obj):
        return obj.get_category_display()

    def get_uploaded_by_email(self, obj):
        return obj.uploaded_by.email if obj.uploaded_by else None


class PublicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        fields = ["title", "category", "year", "description", "file", "published", "order"]

    def validate_title(self, v):
        v = (v or "").strip()
        if not v:
            raise serializers.ValidationError("Title is required.")
        return v

    def validate_file(self, f):
        if f is None:
            raise serializers.ValidationError("A file is required.")
        max_bytes = 50 * 1024 * 1024
        size = getattr(f, "size", 0)
        if size and size > max_bytes:
            raise serializers.ValidationError("File is larger than 50 MB.")
        name = (getattr(f, "name", "") or "").lower()
        allowed = (
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".csv", ".txt", ".png", ".jpg", ".jpeg", ".webp", ".gif",
        )
        if not name.endswith(allowed):
            raise serializers.ValidationError(
                "Unsupported file type. Upload a PDF, Word, Excel, PowerPoint, text, or image file."
            )
        return f

    def create(self, validated):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated["uploaded_by"] = request.user
        return super().create(validated)