from rest_framework import serializers
from .models import SafeguardingReport, SafeguardingNote

class SafeguardingSubmitSerializer(serializers.Serializer):
    reporter_type = serializers.CharField(max_length=64)
    anonymous = serializers.BooleanField(default=False)
    full_name = serializers.CharField(max_length=160, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    relationship = serializers.CharField(max_length=120)
    child_name = serializers.CharField(max_length=160, required=False, allow_blank=True)
    location = serializers.CharField(max_length=200)
    concerns = serializers.ListField(child=serializers.CharField(max_length=64), allow_empty=False)
    urgency = serializers.ChoiceField(choices=["immediate", "urgent", "standard"])
    description = serializers.CharField(min_length=20)
    contact_preference = serializers.CharField(max_length=32)

    def validate(self, attrs):
        if not attrs.get("anonymous"):
            if not attrs.get("full_name", "").strip():
                raise serializers.ValidationError({"full_name": ["Required unless anonymous."]})
            if not attrs.get("phone", "").strip() and not attrs.get("email", "").strip():
                raise serializers.ValidationError({"phone": ["Provide phone or email, or choose anonymous."]})
        return attrs

class SafeguardingReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafeguardingReport
        fields = (
            "id", "reference", "anonymous", "reporter_type", "full_name", "phone", "email",
            "relationship", "child_name", "location", "concerns", "urgency", "status",
            "assigned_to", "internal_notes", "created_at", "updated_at",
        )
        read_only_fields = ("id", "reference", "created_at", "updated_at")

class SafeguardingNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafeguardingNote
        fields = ("id", "report", "author", "body", "created_at")
        read_only_fields = ("id", "author", "created_at")