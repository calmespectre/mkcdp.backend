import base64
import binascii
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from .models import Beneficiary, Sponsorship


MAX_PHOTO_BYTES = 6 * 1024 * 1024


def decode_data_url(value):
    if not value or not isinstance(value, str):
        return None
    if not value.startswith("data:"):
        return None
    try:
        header, encoded = value.split(",", 1)
        mime = header.split(";")[0].replace("data:", "") or "image/jpeg"
        raw = base64.b64decode(encoded)
    except (ValueError, binascii.Error):
        raise serializers.ValidationError("Invalid image data.")
    if len(raw) > MAX_PHOTO_BYTES:
        raise serializers.ValidationError("Image must be smaller than 6 MB.")
    ext = mime.split("/")[-1].lower()
    if ext == "jpeg":
        ext = "jpg"
    return ContentFile(raw, name=f"{uuid.uuid4().hex}.{ext}")


class BeneficiarySerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Beneficiary
        fields = (
            "id",
            "name",
            "age",
            "gender",
            "location",
            "grade",
            "monthly_usd",
            "status",
            "funded",
            "photo",
            "photo_url",
            "dream",
            "story",
            "published",
            "display_order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {
            "photo": {"required": False, "allow_blank": True, "max_length": 20000000},
        }

    def get_photo_url(self, obj):
        if obj.photo_file:
            request = self.context.get("request")
            url = obj.photo_file.url
            return request.build_absolute_uri(url) if request else url
        return obj.photo or ""

    def _handle_photo(self, validated):
        photo = validated.get("photo")
        if isinstance(photo, str) and photo.startswith("data:"):
            validated["photo_file"] = decode_data_url(photo)
            validated["photo"] = ""
        return validated

    def create(self, validated):
        validated = self._handle_photo(validated)
        return super().create(validated)

    def update(self, instance, validated):
        validated = self._handle_photo(validated)
        if validated.get("photo_file"):
            instance.photo_file = validated.pop("photo_file")
            instance.photo = ""
        return super().update(instance, validated)


class SponsorshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sponsorship
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")