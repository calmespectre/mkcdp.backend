from rest_framework import serializers
from .models import GiftNeed, GiftOrder, GiftOrderItem

class GiftNeedSerializer(serializers.ModelSerializer):
    child_image_url = serializers.SerializerMethodField()

    class Meta:
        model = GiftNeed
        fields = ("id", "slug", "title", "body", "category", "price_kes", "child_name", "child_grade", "child_location", "child_image", "child_image_url", "published", "available", "display_order", "stock", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def get_child_image_url(self, obj):
        if obj.child_image_file:
            request = self.context.get("request")
            url = obj.child_image_file.url
            return request.build_absolute_uri(url) if request else url
        return obj.child_image

class GiftOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftOrderItem
        fields = ("id", "need", "quantity", "unit_price_kes", "title_snapshot", "child_name_snapshot")

class GiftOrderSerializer(serializers.ModelSerializer):
    items = GiftOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = GiftOrder
        fields = ("id", "reference", "name", "email", "phone", "currency", "total_kes", "total_local", "status", "payment_method", "items", "created_at", "updated_at")
        read_only_fields = ("id", "reference", "total_kes", "total_local", "status", "created_at", "updated_at")

class GiftOrderCreateItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=50)

class GiftOrderCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    currency = serializers.CharField(max_length=8, default="KES")
    payment_method = serializers.ChoiceField(choices=["mpesa", "card", "bank"])
    items = GiftOrderCreateItemSerializer(many=True)
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("At least one item is required.")
        return items