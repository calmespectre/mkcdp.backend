from rest_framework import serializers
from .models import PartnershipEnquiry

class PartnershipEnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnershipEnquiry
        fields = ("id", "organisation", "contact_name", "email", "phone", "partnership_type", "message", "status", "created_at", "updated_at")
        read_only_fields = ("id", "status", "created_at", "updated_at")