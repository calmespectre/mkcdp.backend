from django.contrib import admin
from .models import GiftNeed, GiftOrder, GiftOrderItem

@admin.register(GiftNeed)
class GiftNeedAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "price_kes", "child_name", "available", "published", "stock")
    list_filter = ("category", "available", "published")
    search_fields = ("title", "child_name", "child_location")

class GiftOrderItemInline(admin.TabularInline):
    model = GiftOrderItem
    extra = 0
    readonly_fields = ("title_snapshot", "unit_price_kes", "quantity", "need")
    can_delete = False

@admin.register(GiftOrder)
class GiftOrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "name", "email", "total_kes", "currency", "payment_method", "status", "created_at")
    list_filter = ("status", "currency", "payment_method")
    search_fields = ("reference", "email", "name")
    inlines = [GiftOrderItemInline]
    readonly_fields = ("id", "reference", "total_kes", "total_local", "created_at", "updated_at")