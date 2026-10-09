from rest_framework import serializers
from .models import SiteContent, ContentRevision

class SiteContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteContent
        fields = ("id", "key", "value", "description", "updated_at")
        read_only_fields = ("id", "updated_at")

class ContentRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentRevision
        fields = ("id", "key", "before", "after", "actor", "created_at")