import uuid
from decimal import Decimal
from django.db import models
from core.models import TimeStampedModel


class GiftNeed(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    category = models.CharField(max_length=80, blank=True)
    price_kes = models.DecimalField(max_digits=12, decimal_places=2)
    child_name = models.CharField(max_length=120)
    child_grade = models.CharField(max_length=80)
    child_location = models.CharField(max_length=120)
    child_image = models.URLField(max_length=500, blank=True)
    child_image_file = models.ImageField(upload_to="gift-needs/", blank=True, null=True)
    published = models.BooleanField(default=True, db_index=True)
    available = models.BooleanField(default=True, db_index=True)
    display_order = models.IntegerField(default=0)
    stock = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["display_order", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price_kes__gte=Decimal("1")),
                name="gift_price_positive",
            ),
        ]

    def __str__(self):
        return self.title


class GiftOrder(TimeStampedModel):
    STATUSES = [
        ("pending", "Pending"),
        ("awaiting_payment", "Awaiting Payment"),
        ("paid", "Paid"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=32, unique=True, db_index=True)
    donor = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="gift_orders",
    )
    name = models.CharField(max_length=160)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=32, blank=True)
    currency = models.CharField(max_length=8, default="KES")
    total_kes = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    total_local = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    exchange_rate = models.DecimalField(max_digits=14, decimal_places=6, default=Decimal("1"))
    payment_method = models.CharField(max_length=16, blank=True)
    status = models.CharField(max_length=24, choices=STATUSES, default="pending", db_index=True)
    idempotency_key = models.CharField(max_length=128, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference

    def recalculate(self):
        total = sum((i.line_total_kes for i in self.items.all()), Decimal("0"))
        self.total_kes = total
        self.total_local = (
            (total / self.exchange_rate).quantize(Decimal("0.01"))
            if self.exchange_rate
            else total
        )
        self.save(update_fields=["total_kes", "total_local", "updated_at"])


class GiftOrderItem(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(GiftOrder, on_delete=models.CASCADE, related_name="items")
    need = models.ForeignKey(GiftNeed, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price_kes = models.DecimalField(max_digits=12, decimal_places=2)
    title_snapshot = models.CharField(max_length=200)
    child_name_snapshot = models.CharField(max_length=120)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="gift_item_qty_positive",
            ),
        ]

    @property
    def line_total_kes(self):
        return (self.unit_price_kes * self.quantity).quantize(Decimal("0.01"))