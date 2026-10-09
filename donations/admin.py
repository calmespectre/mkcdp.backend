from django.contrib import admin
from .models import Donation

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("reference", "full_name", "amount_kes", "requested_currency", "frequency", "payment_method", "status", "created_at")
    list_filter = ("status", "frequency", "payment_method", "requested_currency")
    search_fields = ("reference", "email", "first_name", "last_name", "phone", "receipt_number")
    readonly_fields = ("id", "reference", "created_at", "updated_at", "receipt_number")
    date_hierarchy = "created_at"