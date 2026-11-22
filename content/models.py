from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class SiteContent(TimeStampedModel):
    key = models.CharField(max_length=255, unique=True, db_index=True)
    value = models.JSONField(default=dict, blank=True)
    description = models.CharField(max_length=255, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return self.key


class ChangeSet(TimeStampedModel):
    ACTION_BULK = "bulk"
    ACTION_RESET = "reset"
    ACTION_RESTORE = "restore"
    ACTION_REVERT = "revert"
    ACTION_SNAPSHOT_RESTORE = "snapshot_restore"

    ACTIONS = [
        (ACTION_BULK, "Bulk save"),
        (ACTION_RESET, "Reset"),
        (ACTION_RESTORE, "Restore revision"),
        (ACTION_REVERT, "Revert change set"),
        (ACTION_SNAPSHOT_RESTORE, "Restore snapshot"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="content_changesets",
    )
    action = models.CharField(max_length=32, choices=ACTIONS, default=ACTION_BULK, db_index=True)
    note = models.CharField(max_length=255, blank=True)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    deleted_count = models.PositiveIntegerField(default=0)
    source_changeset = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reverted_by",
    )
    source_revision = models.ForeignKey(
        "ContentRevision",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="restored_by",
    )
    source_snapshot = models.ForeignKey(
        "ContentSnapshot",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="restored_by",
    )

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"ChangeSet #{self.pk} {self.action}"


class ContentRevision(TimeStampedModel):
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"

    ACTIONS = [
        (ACTION_CREATE, "Create"),
        (ACTION_UPDATE, "Update"),
        (ACTION_DELETE, "Delete"),
    ]

    changeset = models.ForeignKey(
        ChangeSet,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="revisions",
    )
    key = models.CharField(max_length=255, db_index=True)
    action = models.CharField(max_length=16, choices=ACTIONS, default=ACTION_UPDATE, db_index=True)
    version = models.PositiveIntegerField(default=1)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["key", "-created_at"], name="content_rev_key_created_idx"),
        ]

    def __str__(self):
        return f"{self.key} v{self.version} {self.action}"


class ContentSnapshot(TimeStampedModel):
    name = models.CharField(max_length=120)
    note = models.CharField(max_length=255, blank=True)
    data = models.JSONField(default=dict)
    key_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="content_snapshots",
    )

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.name
