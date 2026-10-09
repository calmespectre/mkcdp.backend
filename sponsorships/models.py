import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.text import slugify


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Region(TimeStamped):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    country = models.CharField(max_length=80)
    county = models.CharField(max_length=80, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Regions"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:140]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}, {self.country}"


class Guardian(TimeStamped):
    class Relationship(models.TextChoices):
        MOTHER = "mother", "Mother"
        FATHER = "father", "Father"
        GRANDMOTHER = "grandmother", "Grandmother"
        GRANDFATHER = "grandfather", "Grandfather"
        AUNT = "aunt", "Aunt"
        UNCLE = "uncle", "Uncle"
        SIBLING = "sibling", "Sibling"
        OTHER = "other", "Other"

    full_name = models.CharField(max_length=160)
    relationship = models.CharField(max_length=20, choices=Relationship.choices)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    occupation = models.CharField(max_length=120, blank=True)
    household_size = models.PositiveIntegerField(default=1)
    monthly_income_usd = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.get_relationship_display()})"


class Child(TimeStamped):
    class Gender(models.TextChoices):
        FEMALE = "Female", "Female"
        MALE = "Male", "Male"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        AVAILABLE = "available", "Available"
        PENDING = "pending", "Pending Sponsorship"
        SPONSORED = "sponsored", "Sponsored"
        GRADUATED = "graduated", "Graduated"
        ARCHIVED = "archived", "Archived"

    class EducationLevel(models.TextChoices):
        NONE = "none", "Not in school"
        PRESCHOOL = "preschool", "Preschool"
        PRIMARY = "primary", "Primary"
        SECONDARY = "secondary", "Secondary"
        VOCATIONAL = "vocational", "Vocational"
        UNIVERSITY = "university", "University"

    reference_code = models.CharField(max_length=24, unique=True, blank=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)

    name = models.CharField(max_length=120)
    gender = models.CharField(max_length=10, choices=Gender.choices)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=120, blank=True)

    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    location = models.CharField(max_length=160, blank=True)
    guardian = models.ForeignKey(
        Guardian,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    siblings_count = models.PositiveIntegerField(default=0)

    education_level = models.CharField(
        max_length=20, choices=EducationLevel.choices, default=EducationLevel.PRIMARY
    )
    grade = models.CharField(max_length=80, blank=True)
    school_name = models.CharField(max_length=160, blank=True)

    monthly_cost_usd = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("39.00"),
        validators=[MinValueValidator(Decimal("1.00"))],
    )
    funding_goal_usd = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE, db_index=True
    )
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_children",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    dream = models.CharField(max_length=200, blank=True)
    interests = models.CharField(max_length=240, blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["status", "gender"]),
            models.Index(fields=["region", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "child"
            candidate = base
            i = 1
            while Child.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                i += 1
                candidate = f"{base}-{i}"
            self.slug = candidate[:180]
        if not self.reference_code:
            year = timezone.now().year
            prefix = f"CH-{year}-"
            last = (
                Child.objects.filter(reference_code__startswith=prefix)
                .order_by("-reference_code")
                .values_list("reference_code", flat=True)
                .first()
            )
            seq = 1
            if last:
                try:
                    seq = int(last.split("-")[-1]) + 1
                except ValueError:
                    seq = 1
            self.reference_code = f"{prefix}{seq:04d}"
        super().save(*args, **kwargs)

    @property
    def age(self):
        today = timezone.now().date()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    @property
    def primary_photo(self):
        photo = self.photos.filter(is_primary=True).first() or self.photos.first()
        return photo.image if photo else None

    @property
    def primary_photo_url(self):
        photo = self.primary_photo
        return photo.url if photo else ""

    @property
    def active_sponsorships_count(self):
        return self.sponsorships.filter(active=True).count()

    @property
    def monthly_raised_usd(self):
        total = self.sponsorships.filter(active=True).aggregate(
            total=Sum("monthly_amount_usd")
        )["total"]
        return total or Decimal("0.00")

    @property
    def funded_percent(self):
        if not self.monthly_cost_usd or self.monthly_cost_usd <= 0:
            return 0
        pct = (self.monthly_raised_usd / self.monthly_cost_usd) * Decimal("100")
        return min(int(pct), 100)

    @property
    def is_sponsored(self):
        return self.status == self.Status.SPONSORED or self.active_sponsorships_count > 0

    def __str__(self):
        return f"{self.name} ({self.reference_code})"


class ChildPhoto(TimeStamped):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="children/photos/")
    caption = models.CharField(max_length=180, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["child"],
                condition=Q(is_primary=True),
                name="unique_primary_photo_per_child",
            )
        ]

    def save(self, *args, **kwargs):
        if self.is_primary:
            ChildPhoto.objects.filter(child=self.child, is_primary=True).exclude(
                pk=self.pk
            ).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Photo for {self.child.name}"


class NeedCategory(TimeStamped):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Need categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:100]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ChildNeed(TimeStamped):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="needs")
    category = models.ForeignKey(
        NeedCategory,
        on_delete=models.PROTECT,
        related_name="needs",
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    amount_usd = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    is_recurring = models.BooleanField(default=False)
    is_fulfilled = models.BooleanField(default=False)
    fulfilled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-priority", "title"]
        indexes = [models.Index(fields=["child", "is_fulfilled"])]

    def __str__(self):
        return f"{self.title} — {self.child.name}"


class ChildUpdate(TimeStamped):
    class UpdateType(models.TextChoices):
        PROGRESS = "progress", "Progress report"
        SCHOOL = "school", "School update"
        HEALTH = "health", "Health update"
        MILESTONE = "milestone", "Milestone"
        LETTER = "letter", "Letter"
        GENERAL = "general", "General"

    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="updates")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_updates",
    )
    update_type = models.CharField(
        max_length=20, choices=UpdateType.choices, default=UpdateType.GENERAL
    )
    title = models.CharField(max_length=180)
    body = models.TextField()
    is_public = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.child.name}"


class ChildWish(TimeStamped):
    class Occasion(models.TextChoices):
        BIRTHDAY = "birthday", "Birthday"
        CHRISTMAS = "christmas", "Christmas"
        SCHOOL = "school", "Back to school"
        OTHER = "other", "Other"

    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="wishes")
    occasion = models.CharField(max_length=20, choices=Occasion.choices)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    amount_usd = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    is_granted = models.BooleanField(default=False)
    granted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.child.name}"


class SponsorshipPlan(TimeStamped):
    class Interval(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        ANNUAL = "annual", "Annual"

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    amount_usd = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("1.00"))]
    )
    interval = models.CharField(
        max_length=20, choices=Interval.choices, default=Interval.MONTHLY
    )
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["amount_usd"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:100]
        if self.is_default:
            SponsorshipPlan.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.amount_usd} USD / {self.interval})"


class Sponsorship(TimeStamped):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    reference = models.CharField(max_length=40, unique=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sponsorships",
    )
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name="sponsorships",
    )
    plan = models.ForeignKey(
        SponsorshipPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sponsorships",
    )
    monthly_amount_usd = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("1.00"))]
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    active = models.BooleanField(default=True, db_index=True)
    auto_renew = models.BooleanField(default=True)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    next_billing_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "child"],
                condition=Q(active=True),
                name="unique_active_sponsorship_per_user_child",
            )
        ]
        indexes = [
            models.Index(fields=["user", "active"]),
            models.Index(fields=["child", "active"]),
        ]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"SP-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    @property
    def total_paid_usd(self):
        total = self.payments.filter(status=SponsorshipPayment.Status.COMPLETED).aggregate(
            total=Sum("amount_usd")
        )["total"]
        return total or Decimal("0.00")

    def __str__(self):
        return f"{self.user} → {self.child.name} ({self.status})"


class SponsorshipPayment(TimeStamped):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    class Method(models.TextChoices):
        CARD = "card", "Card"
        MPESA = "mpesa", "M-Pesa"
        BANK = "bank", "Bank transfer"
        PAYPAL = "paypal", "PayPal"
        OTHER = "other", "Other"

    reference = models.CharField(max_length=60, unique=True, blank=True)
    sponsorship = models.ForeignKey(
        Sponsorship,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount_usd = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    currency = models.CharField(max_length=8, default="USD")
    amount_local = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    method = models.CharField(
        max_length=20, choices=Method.choices, default=Method.CARD
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    gateway_reference = models.CharField(max_length=120, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    failure_reason = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["sponsorship", "status"])]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        if self.status == self.Status.COMPLETED and not self.paid_at:
            self.paid_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} · {self.amount_usd} {self.currency}"


class Letter(TimeStamped):
    class Sender(models.TextChoices):
        SPONSOR = "sponsor", "Sponsor"
        CHILD = "child", "Child"
        STAFF = "staff", "Staff"

    sponsorship = models.ForeignKey(
        Sponsorship,
        on_delete=models.CASCADE,
        related_name="letters",
    )
    sender = models.CharField(max_length=10, choices=Sender.choices)
    subject = models.CharField(max_length=180, blank=True)
    body = models.TextField()
    attachment = models.FileField(upload_to="letters/", blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_letters",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_sender_display()} letter · {self.sponsorship.reference}"