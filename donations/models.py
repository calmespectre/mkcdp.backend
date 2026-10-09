import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from core.models import TimeStampedModel


class Donation(TimeStampedModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]
    FREQ_CHOICES = [("once", "One-time"), ("monthly", "Monthly")]
    METHOD_CHOICES = [("mpesa", "M-Pesa"), ("card", "Card"), ("bank", "Bank Transfer")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=32, unique=True, db_index=True)
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="donations",
    )
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=32)
    amount_kes = models.DecimalField(max_digits=14, decimal_places=2, db_index=True)
    requested_amount = models.DecimalField(max_digits=14, decimal_places=2)
    requested_currency = models.CharField(max_length=8, default="KES")
    exchange_rate = models.DecimalField(max_digits=14, decimal_places=6, default=Decimal("1"))
    frequency = models.CharField(max_length=16, choices=FREQ_CHOICES, default="once", db_index=True)
    payment_method = models.CharField(max_length=16, choices=METHOD_CHOICES, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", db_index=True)
    impact_note = models.CharField(max_length=255, blank=True)
    receipt_number = models.CharField(max_length=32, blank=True, db_index=True)
    idempotency_key = models.CharField(max_length=128, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "frequency"]),
            models.Index(fields=["payment_method", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_kes__gte=Decimal("100")),
                name="donation_min_100_kes",
            ),
        ]

    def __str__(self):
        return f"{self.reference} {self.amount_kes} {self.requested_currency}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class RecurringDonation(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    donation = models.ForeignKey(
        Donation, on_delete=models.CASCADE, related_name="recurring_children"
    )
    parent = models.ForeignKey(
        Donation, on_delete=models.CASCADE, related_name="recurring_instances"
    )
    scheduled_for = models.DateField(db_index=True)
    processed = models.BooleanField(default=False)