import uuid
from django.db import models
from core.models import TimeStampedModel

class SafeguardingReport(TimeStampedModel):
    URGENCY = [("immediate", "Immediate"), ("urgent", "Urgent"), ("standard", "Standard")]
    STATUSES = [("new", "New"), ("triage", "Triage"), ("investigating", "Investigating"), ("resolved", "Resolved"), ("closed", "Closed")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=32, unique=True, db_index=True)
    anonymous = models.BooleanField(default=False)
    reporter_type = models.CharField(max_length=64)
    full_name = models.CharField(max_length=160, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    relationship = models.CharField(max_length=120)
    child_name = models.CharField(max_length=160, blank=True)
    location = models.CharField(max_length=200)
    concerns = models.JSONField(default=list, blank=True)
    urgency = models.CharField(max_length=16, choices=URGENCY)
    description = models.TextField()
    contact_preference = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=16, choices=STATUSES, default="new", db_index=True)
    assigned_to = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_reports")
    internal_notes = models.TextField(blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference

class SafeguardingNote(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(SafeguardingReport, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    body = models.TextField()