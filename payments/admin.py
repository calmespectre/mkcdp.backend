from django.contrib import admin
from .models import Payment, PaymentEvent

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("public_reference", "method", "provider", "amount", "amount_kes", "status", "paid_at", "created_at")
    list_filter = ("status", "method", "provider")
    search_fields = ("public_reference", "provider_transaction_id", "provider_checkout_id", "bank_reference")
    readonly_fields = ("id", "public_reference", "created_at", "updated_at", "paid_at", "provider_response")
    date_hierarchy = "created_at"

@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    list_display = ("payment", "event_type", "processed", "created_at")
    list_filter = ("event_type", "processed")
    search_fields = ("payment__public_reference", "idempotency_key")