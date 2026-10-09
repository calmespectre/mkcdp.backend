import logging
import stripe
from django.conf import settings
from django.utils import timezone
from .base import PaymentProvider

logger = logging.getLogger(__name__)

class CardProvider(PaymentProvider):
    name = "stripe"
    method = "card"

    def __init__(self):
        stripe.api_key = settings.CARD["SECRET_KEY"]

    def initiate(self, payment):
        amount_minor = int((payment.amount_kes * 100).quantize(1))
        metadata = {"public_reference": payment.public_reference}
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_minor,
                currency="kes",
                metadata=metadata,
                automatic_payment_methods={"enabled": True},
            )
            payment.provider_transaction_id = intent.id
            payment.provider_response = {"client_secret": intent.client_secret, "status": intent.status}
            payment.status = "processing"
        except stripe.error.StripeError as e:
            payment.status = "failed"
            payment.failure_reason = str(e)[:250]
            logger.exception("Stripe payment intent error")
        payment.save()
        return payment

    def handle_webhook(self, event):
        from payments.models import Payment
        intent = event["data"]["object"]
        ref = (intent.get("metadata") or {}).get("public_reference")
        payment = Payment.objects.filter(public_reference=ref).first()
        if not payment:
            return None
        if payment.status in ("completed", "refunded"):
            return payment
        event_type = event.get("type", "")
        payment.provider_response = {**(payment.provider_response or {}), "webhook_type": event_type, "intent_status": intent.get("status")}
        if event_type == "payment_intent.succeeded":
            payment.status = "completed"
            payment.paid_at = timezone.now()
            payment.provider_transaction_id = intent.get("id", payment.provider_transaction_id)
        elif event_type in ("payment_intent.payment_failed", "payment_intent.canceled"):
            payment.status = "failed"
            payment.failure_reason = (intent.get("last_payment_error") or {}).get("message", "Card payment failed")[:250]
        payment.save()
        return payment