from django.conf import settings
from django.db import models


class Letter(models.Model):
    DIRECTION_CHOICES = (
        ("in", "Inbox"),
        ("out", "Sent"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="letters",
    )
    child = models.ForeignKey(
        "sponsorships.Child",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="letters",
    )
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    direction = models.CharField(max_length=8, choices=DIRECTION_CHOICES, default="out")
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject or f"Letter #{self.pk}"