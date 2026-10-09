from django.conf import settings
from django.db import models
from core.models import TimeStampedModel

class SiteContent(TimeStampedModel):
    key = models.CharField(max_length=255, unique=True, db_index=True)
    value = models.JSONField(default=dict, blank=True)
    description = models.CharField(max_length=255, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return self.key

class ContentRevision(TimeStampedModel):
    key = models.CharField(max_length=255, db_index=True)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-created_at"]