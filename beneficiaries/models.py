import uuid
from django.db import models
from core.models import TimeStampedModel


class Beneficiary(TimeStampedModel):
    STATUSES = [
        ("Available", "Available"),
        ("Sponsored", "Sponsored"),
        ("Inactive", "Inactive"),
    ]
    GENDERS = [("Female", "Female"), ("Male", "Male"), ("Other", "Other")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=16, choices=GENDERS, default="Female")
    location = models.CharField(max_length=160)
    grade = models.CharField(max_length=80)
    monthly_usd = models.DecimalField(max_digits=10, decimal_places=2, default=39)
    status = models.CharField(max_length=16, choices=STATUSES, default="Available", db_index=True)
    funded = models.PositiveIntegerField(default=0)
    photo = models.CharField(max_length=2000, blank=True)
    photo_file = models.ImageField(upload_to="beneficiaries/", blank=True, null=True)
    dream = models.CharField(max_length=255, blank=True)
    story = models.TextField(blank=True)
    published = models.BooleanField(default=True, db_index=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order", "-created_at"]
        indexes = [models.Index(fields=["status", "published"])]

    def __str__(self):
        return self.name


class Sponsorship(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.PROTECT, related_name="sponsorships")
    sponsor = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="sponsorships")
    donor_email = models.EmailField()
    donor_name = models.CharField(max_length=160)
    monthly_usd = models.DecimalField(max_digits=10, decimal_places=2)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True, db_index=True)