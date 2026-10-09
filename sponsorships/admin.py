from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Child,
    ChildNeed,
    ChildPhoto,
    ChildUpdate,
    ChildWish,
    Guardian,
    Letter,
    NeedCategory,
    Region,
    Sponsorship,
    SponsorshipPayment,
    SponsorshipPlan,
)


class ChildPhotoInline(admin.TabularInline):
    model = ChildPhoto
    extra = 1


class ChildNeedInline(admin.TabularInline):
    model = ChildNeed
    extra = 0


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "county", "is_active")
    search_fields = ("name", "country", "county")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ("full_name", "relationship", "phone", "household_size")
    search_fields = ("full_name", "phone")
    list_filter = ("relationship",)


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = (
        "reference_code",
        "name",
        "age_display",
        "gender",
        "region",
        "status",
        "monthly_cost_usd",
        "funded_display",
        "is_verified",
    )
    list_filter = ("status", "gender", "region", "education_level", "is_verified")
    search_fields = ("name", "reference_code", "location", "school_name")
    readonly_fields = ("reference_code", "slug", "created_at", "updated_at", "photo_preview")
    inlines = [ChildPhotoInline, ChildNeedInline]
    fieldsets = (
        ("Identity", {"fields": ("reference_code", "slug", "name", "gender", "date_of_birth", "place_of_birth")}),
        ("Location", {"fields": ("region", "location", "guardian", "siblings_count")}),
        ("Education", {"fields": ("education_level", "grade", "school_name")}),
        ("Funding", {"fields": ("monthly_cost_usd", "funding_goal_usd")}),
        ("Story", {"fields": ("dream", "interests", "bio")}),
        ("Status", {"fields": ("status", "is_verified", "verified_by", "verified_at")}),
        ("Preview", {"fields": ("photo_preview",)}),
    )

    def age_display(self, obj):
        return obj.age

    age_display.short_description = "Age"

    def funded_display(self, obj):
        return f"{obj.funded_percent}%"

    funded_display.short_description = "Funded"

    def photo_preview(self, obj):
        url = obj.primary_photo_url
        if not url:
            return "—"
        return format_html('<img src="{}" style="max-height:160px;border-radius:8px;" />', url)


@admin.register(ChildPhoto)
class ChildPhotoAdmin(admin.ModelAdmin):
    list_display = ("child", "caption", "is_primary", "order")
    list_filter = ("is_primary",)


@admin.register(NeedCategory)
class NeedCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ChildNeed)
class ChildNeedAdmin(admin.ModelAdmin):
    list_display = ("title", "child", "category", "amount_usd", "priority", "is_fulfilled")
    list_filter = ("priority", "is_fulfilled", "category")
    search_fields = ("title", "child__name")


@admin.register(ChildUpdate)
class ChildUpdateAdmin(admin.ModelAdmin):
    list_display = ("title", "child", "update_type", "is_public", "created_at")
    list_filter = ("update_type", "is_public")
    search_fields = ("title", "child__name")


@admin.register(ChildWish)
class ChildWishAdmin(admin.ModelAdmin):
    list_display = ("title", "child", "occasion", "amount_usd", "is_granted")
    list_filter = ("occasion", "is_granted")


@admin.register(SponsorshipPlan)
class SponsorshipPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "amount_usd", "interval", "is_active", "is_default")
    prepopulated_fields = {"slug": ("name",)}


class SponsorshipPaymentInline(admin.TabularInline):
    model = SponsorshipPayment
    extra = 0
    readonly_fields = ("reference", "created_at")


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "user",
        "child",
        "monthly_amount_usd",
        "status",
        "active",
        "started_at",
    )
    list_filter = ("status", "active", "auto_renew")
    search_fields = ("reference", "user__email", "child__name")
    readonly_fields = ("reference", "created_at", "updated_at")
    inlines = [SponsorshipPaymentInline]


@admin.register(SponsorshipPayment)
class SponsorshipPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "sponsorship",
        "amount_usd",
        "currency",
        "method",
        "status",
        "paid_at",
    )
    list_filter = ("status", "method", "currency")
    search_fields = ("reference", "gateway_reference", "sponsorship__reference")
    readonly_fields = ("reference", "created_at")


@admin.register(Letter)
class LetterAdmin(admin.ModelAdmin):
    list_display = ("sponsorship", "sender", "subject", "is_approved", "is_read", "created_at")
    list_filter = ("sender", "is_approved", "is_read")
    search_fields = ("subject", "sponsorship__reference")