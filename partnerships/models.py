import uuid
from django.db import models
from core.models import TimeStampedModel

class PartnershipEnquiry(TimeStampedModel):
    STATUSES = [("new", "New"), ("contacted", "Contacted"), ("in_discussion", "In Discussion"), ("partnered", "Partnered"), ("declined", "Declined"), ("archived", "Archived")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=160)
    email = models.EmailField()
    phone = models.CharField(max_length=32, blank=True)
    partnership_type = models.CharField(max_length=120)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUSES, default="new", db_index=True)
    internal_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]