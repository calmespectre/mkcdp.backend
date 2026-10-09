import uuid
from decimal import Decimal
from django.db import models
from core.models import TimeStampedModel


class Payment(TimeStampedModel):
    PROVIDERS = [("mpesa", "M-Pesa"), ("stripe", "Stripe"), ("bank", "Bank")]
    METHODS = [("mpesa", "M-Pesa"), ("card", "Card"), ("bank", "Bank Transfer")]
    STATUSES = [
        ("pending", "Pending"),
        ("initiated", "Initiated"),
        ("processing", "Processing"),
        ("pending_verification", "Pending Verification"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_reference = models.CharField(max_length=40, unique=True, db_index=True)
    donation = models.ForeignKey(
        "donations.Donation",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    gift_order = models.ForeignKey(
        "gifts.GiftOrder",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    provider = models.CharField(max_length=16, choices=PROVIDERS, db_index=True)
    method = models.CharField(max_length=16, choices=METHODS, db_index=True)
    currency = models.CharField(max_length=8, default="KES")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    amount_kes = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=24, choices=STATUSES, default="pending", db_index=True)
    provider_transaction_id = models.CharField(max_length=128, blank=True, db_index=True)
    provider_checkout_id = models.CharField(max_length=128, blank=True, db_index=True)
    provider_response = models.JSONField(default=dict, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    receipt_number = models.CharField(max_length=32, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=128, blank=True, db_index=True)
    bank_reference = models.CharField(max_length=40, blank=True)
    bank_verified_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bank_verifications",
    )
    bank_verified_at = models.DateTimeField(null=True, blank=True)
    bank_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "method"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=Decimal("0")),
                name="payment_amount_nonneg",
            ),
        ]

    def __str__(self):
        return f"{self.public_reference} {self.method} {self.amount} {self.status}"

    def next_action(self):
        if self.method == "mpesa":
            return {
                "type": "mpesa_stk_push",
                "message": "Check your phone for the M-Pesa prompt.",
            }
        if self.method == "card":
            return {
                "type": "card_checkout",
                "client_secret": (self.provider_response or {}).get("client_secret", ""),
            }
        if self.method == "bank":
            return {
                "type": "bank_transfer",
                "instructions": (self.provider_response or {}).get("instructions", {}),
            }
        return {"type": "none"}


class PaymentEvent(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    processed = models.BooleanField(default=False)
    idempotency_key = models.CharField(max_length=128, blank=True, db_index=True)