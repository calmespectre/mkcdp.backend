from rest_framework import serializers
from .models import Payment, PaymentEvent

class PaymentSerializer(serializers.ModelSerializer):
    next_action = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = (
            "id", "public_reference", "method", "provider", "currency",
            "amount", "amount_kes", "status", "provider_transaction_id",
            "provider_checkout_id", "failure_reason", "receipt_number",
            "paid_at", "bank_reference", "created_at", "updated_at", "next_action",
        )

    def get_next_action(self, obj):
        return obj.next_action()

class PaymentEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentEvent
        fields = ("id", "event_type", "processed", "created_at")

class BankVerifySerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    notes = serializers.CharField(required=False, allow_blank=True)
    receipt_number = serializers.CharField(required=False, allow_blank=True)