from decimal import Decimal
from rest_framework import serializers
from .models import Donation
from core.utils import to_decimal

CURRENCY_RATES = {
    "KES": Decimal("1"),
    "USD": Decimal("129"),
    "EUR": Decimal("140"),
    "GBP": Decimal("163"),
    "ZAR": Decimal("7.1"),
    "UGX": Decimal("0.034"),
    "TZS": Decimal("0.048"),
    "RWF": Decimal("0.094"),
    "AED": Decimal("35.1"),
    "SAR": Decimal("34.4"),
    "CAD": Decimal("94.5"),
    "AUD": Decimal("85.2"),
    "INR": Decimal("1.55"),
    "CNY": Decimal("17.9"),
    "JPY": Decimal("0.85"),
    "CHF": Decimal("146"),
}

class DonationSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    amount_local = serializers.SerializerMethodField()

    class Meta:
        model = Donation
        fields = (
            "id", "reference", "first_name", "last_name", "full_name", "email", "phone",
            "amount_kes", "requested_amount", "requested_currency", "exchange_rate",
            "amount_local", "frequency", "payment_method", "status", "impact_note",
            "receipt_number", "created_at", "updated_at",
        )
        read_only_fields = ("id", "reference", "amount_kes", "exchange_rate", "status", "receipt_number", "created_at", "updated_at")

    def get_amount_local(self, obj):
        return str(obj.requested_amount)

class DonationCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=80)
    last_name = serializers.CharField(max_length=80)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=32)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    currency = serializers.CharField(max_length=8, default="KES")
    frequency = serializers.ChoiceField(choices=["once", "monthly"], default="once")
    payment_method = serializers.ChoiceField(choices=["mpesa", "card", "bank"])
    impact_note = serializers.CharField(max_length=255, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True)

    def validate(self, attrs):
        amount = to_decimal(attrs["amount"])
        currency = attrs["currency"].upper()
        rate = CURRENCY_RATES.get(currency)
        if rate is None:
            raise serializers.ValidationError({"currency": ["Unsupported currency."]})
        kes = (amount * rate).quantize(Decimal("0.01"))
        if kes < Decimal("100"):
            raise serializers.ValidationError({"amount": ["Minimum gift is KES 100."]})
        if attrs["payment_method"] == "mpesa":
            from core.utils import is_valid_kenyan_msisdn
            if not is_valid_kenyan_msisdn(attrs["phone"]):
                raise serializers.ValidationError({"phone": ["Valid Kenyan phone number required for M-Pesa."]})
        attrs["amount_kes"] = kes
        attrs["requested_amount"] = amount
        attrs["requested_currency"] = currency
        attrs["exchange_rate"] = rate
        return attrs