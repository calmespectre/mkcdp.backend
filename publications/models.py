import uuid
from django.conf import settings
from django.db import models
from django.utils.text import slugify
from core.models import TimeStampedModel


class Publication(TimeStampedModel):
    CATEGORIES = [
        ("annual-report", "Annual Report"),
        ("financial-statement", "Financial Statement"),
        ("strategic-plan", "Strategic Plan"),
        ("impact-report", "Impact Report"),
        ("newsletter", "Newsletter"),
        ("policy", "Policy Document"),
        ("other", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.CharField(max_length=40, choices=CATEGORIES, default="other", db_index=True)
    year = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="publications/%Y/%m/")
    file_size = models.PositiveBigIntegerField(default=0)
    file_type = models.CharField(max_length=16, blank=True)
    published = models.BooleanField(default=True, db_index=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="publications",
    )

    class Meta:
        ordering = ["-year", "-created_at"]
        indexes = [models.Index(fields=["published", "category"])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                self.file_size = 0
        if self.file and not self.file_type:
            name = self.file.name or ""
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            self.file_type = ext
        if not self.slug:
            base = slugify(self.title)[:200] or "publication"
            slug = base
            n = 1
            while Publication.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def category_label(self):
        return dict(self.CATEGORIES).get(self.category, self.category)

    @property
    def file_size_display(self):
        size = self.file_size or 0
        if size <= 0:
            return ""
        units = ["B", "KB", "MB", "GB"]
        i = 0
        s = float(size)
        while s >= 1024 and i < len(units) - 1:
            s /= 1024
            i += 1
        return f"{s:.0f} {units[i]}" if i == 0 else f"{s:.1f} {units[i]}"