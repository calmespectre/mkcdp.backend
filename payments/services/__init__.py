from django.db import transaction
from .mpesa import MpesaProvider
from .card import CardProvider
from .bank import BankProvider
from core.utils import reference
from ..models import Payment

PROVIDERS = {
    "mpesa": MpesaProvider,
    "card": CardProvider,
    "bank": BankProvider,
}

def get_provider(method):
    klass = PROVIDERS.get(method)
    if not klass:
        raise ValueError(f"Unsupported payment method: {method}")
    return klass()

def initiate_payment(*, donation=None, gift_order=None, method):
    provider = get_provider(method)
    amount_kes = donation.amount_kes if donation else gift_order.total_kes
    amount = donation.requested_amount if donation else gift_order.total_local
    currency = donation.requested_currency if donation else gift_order.currency
    with transaction.atomic():
        payment = Payment.objects.create(
            public_reference=reference("PAY"),
            donation=donation,
            gift_order=gift_order,
            provider=provider.name,
            method=provider.method,
            currency=currency,
            amount=amount,
            amount_kes=amount_kes,
            status="pending",
        )
    try:
        provider.initiate(payment)
    except Exception as e:
        payment.status = "failed"
        payment.failure_reason = str(e)[:250]
        payment.save(update_fields=["status", "failure_reason", "updated_at"])
        raise
    if donation:
        donation.status = "processing" if payment.status in ("processing", "pending_verification") else payment.status
        donation.save(update_fields=["status", "updated_at"])
    return payment

def mark_payment_completed(payment, receipt=None):
    from django.utils import timezone
    if payment.status == "completed":
        return payment
    payment.status = "completed"
    payment.paid_at = timezone.now()
    if receipt and not payment.receipt_number:
        payment.receipt_number = receipt
    payment.save()
    _propagate_completion(payment)
    return payment

def _propagate_completion(payment):
    from payments.tasks import broadcast_payment_status, send_payment_receipt
    if payment.donation:
        donation = payment.donation
        if donation.status != "completed":
            donation.status = "completed"
            if payment.receipt_number:
                donation.receipt_number = payment.receipt_number
            donation.save(update_fields=["status", "receipt_number", "updated_at"])
    if payment.gift_order:
        order = payment.gift_order
        if order.status != "paid":
            order.status = "paid"
            order.save(update_fields=["status", "updated_at"])
    broadcast_payment_status.delay(str(payment.id))
    send_payment_receipt.delay(str(payment.id))