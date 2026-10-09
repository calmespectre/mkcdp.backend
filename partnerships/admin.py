from django.contrib import admin
from .models import PartnershipEnquiry

@admin.register(PartnershipEnquiry)
class PartnershipEnquiryAdmin(admin.ModelAdmin):
    list_display = ("organisation", "contact_name", "email", "partnership_type", "status", "created_at")
    list_filter = ("status", "partnership_type")
    search_fields = ("organisation", "contact_name", "email", "phone")