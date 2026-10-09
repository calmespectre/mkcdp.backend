from django.conf import settings
from django.db import models


class SiteContentEdit(models.Model):
    key = models.CharField(max_length=512, unique=True, db_index=True)
    value = models.JSONField()
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="site_content_edits",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key"]
        verbose_name = "Site content edit"
        verbose_name_plural = "Site content edits"

    def __str__(self):
        return self.key


class SiteContentVersion(models.Model):
    snapshot = models.JSONField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="site_content_versions",
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Site content version"
        verbose_name_plural = "Site content versions"

    def __str__(self):
        return f"Snapshot #{self.pk} · {self.created_at:%Y-%m-%d %H:%M}"