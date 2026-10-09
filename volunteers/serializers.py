from rest_framework import serializers
from .models import Opportunity, VolunteerApplication

class OpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Opportunity
        fields = ("id", "code", "org", "title", "location", "commitment", "start_date", "deadline", "description", "skills", "tags", "published", "archived", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

class VolunteerApplicationSerializer(serializers.ModelSerializer):
    opportunity_title = serializers.CharField(source="opportunity.title", read_only=True)

    class Meta:
        model = VolunteerApplication
        fields = ("id", "opportunity", "opportunity_title", "full_name", "phone", "email", "availability", "note", "status", "created_at", "updated_at")
        read_only_fields = ("id", "status", "created_at", "updated_at")

class VolunteerApplicationCreateSerializer(serializers.Serializer):
    opportunity_id = serializers.UUIDField()
    full_name = serializers.CharField(max_length=160)
    phone = serializers.CharField(max_length=32)
    email = serializers.EmailField(required=False, allow_blank=True)
    availability = serializers.CharField(max_length=64)
    note = serializers.CharField(required=False, allow_blank=True)