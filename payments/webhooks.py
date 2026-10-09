import hashlib
import hmac
import json
import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Payment, PaymentEvent
from .services import mark_payment_completed
from .services.mpesa import MpesaProvider
from .services.card import CardProvider

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def mpesa_webhook(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")
    logger.info("M-Pesa callback: %s", payload)
    provider = MpesaProvider()
    payment = provider.handle_webhook(payload)
    if payment and payment.status == "completed":
        event_key = f"mpesa:{payment.provider_transaction_id}"
        _, created = PaymentEvent.objects.get_or_create(payment=payment, event_type="mpesa_callback", idempotency_key=event_key, defaults={"payload": payload, "processed": True})
        if created:
            mark_payment_completed(payment, receipt=payment.provider_transaction_id)
    return HttpResponse("OK")

@csrf_exempt
@require_POST
def card_webhook(request):
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    secret = settings.CARD["WEBHOOK_SECRET"]
    if not secret:
        return HttpResponseBadRequest("Webhook secret not configured")
    import stripe
    try:
        event = stripe.Webhook.construct_event(request.body, sig_header, secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        logger.warning("Invalid Stripe webhook signature")
        return HttpResponseBadRequest("Invalid signature")
    provider = CardProvider()
    payment = provider.handle_webhook(event)
    if payment:
        _, created = PaymentEvent.objects.get_or_create(payment=payment, event_type=f"card_{event['type']}", idempotency_key=event.get("id", ""), defaults={"payload": event, "processed": True})
        if created and payment.status == "completed":
            mark_payment_completed(payment)
    return HttpResponse("OK")