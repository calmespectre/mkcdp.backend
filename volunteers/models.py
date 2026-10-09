import uuid
from django.db import models
from core.models import TimeStampedModel

class Opportunity(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, unique=True)
    org = models.CharField(max_length=160)
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=160)
    commitment = models.CharField(max_length=160)
    start_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    description = models.TextField()
    skills = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    published = models.BooleanField(default=True, db_index=True)
    archived = models.BooleanField(default=False, db_index=True)
    created_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} {self.title}"

class VolunteerApplication(TimeStampedModel):
    STATUSES = [("new", "New"), ("reviewing", "Reviewing"), ("shortlisted", "Shortlisted"), ("accepted", "Accepted"), ("rejected", "Rejected"), ("archived", "Archived")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opportunity = models.ForeignKey(Opportunity, on_delete=models.PROTECT, related_name="applications")
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=32)
    email = models.EmailField(blank=True)
    availability = models.CharField(max_length=64)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUSES, default="new", db_index=True)
    internal_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]