import os
from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Publication(models.Model):
    CATEGORY_ANNUAL = "annual-report"
    CATEGORY_FINANCIAL = "financial-statement"
    CATEGORY_STRATEGIC = "strategic-plan"
    CATEGORY_IMPACT = "impact-report"
    CATEGORY_NEWSLETTER = "newsletter"
    CATEGORY_POLICY = "policy"
    CATEGORY_OTHER = "other"

    CATEGORY_CHOICES = [
        (CATEGORY_ANNUAL, "Annual Report"),
        (CATEGORY_FINANCIAL, "Financial Statement"),
        (CATEGORY_STRATEGIC, "Strategic Plan"),
        (CATEGORY_IMPACT, "Impact Report"),
        (CATEGORY_NEWSLETTER, "Newsletter"),
        (CATEGORY_POLICY, "Policy Document"),
        (CATEGORY_OTHER, "Other"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default=CATEGORY_ANNUAL)
    year = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="publications/%Y/")
    file_size = models.PositiveBigIntegerField(default=0)
    file_type = models.CharField(max_length=80, blank=True)
    published = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="publications_uploaded",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "order", "-created_at"]
        verbose_name = "Publication"
        verbose_name_plural = "Publications"

    def __str__(self):
        return f"{self.title} ({self.year or 'n/a'})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:250] or "publication"
            slug = base
            n = 1
            while Publication.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug

        if self.file:
            try:
                self.file_size = self.file.size
            except Exception:
                self.file_size = self.file_size or 0

            name = getattr(self.file, "name", "") or ""
            ext = os.path.splitext(name)[1].lower().lstrip(".")
            if ext:
                self.file_type = ext

        super().save(*args, **kwargs)