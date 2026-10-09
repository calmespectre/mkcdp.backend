from django.contrib import admin
from .models import Beneficiary, Sponsorship

@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ("name", "age", "gender", "location", "grade", "monthly_usd", "status", "funded", "published")
    list_filter = ("status", "gender", "published")
    search_fields = ("name", "location", "grade")

@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = ("donor_name", "beneficiary", "monthly_usd", "active", "started_at")
    list_filter = ("active",)
    search_fields = ("donor_name", "donor_email", "beneficiary__name")