import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from celery import shared_task

logger = logging.getLogger(__name__)

def _broadcast(group, payload):
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(group, {"type": "payment.status", "payload": payload})

def _broadcast_admin(payload):
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)("admin_events", {"type": "admin_event", "payload": payload})

@shared_task
def broadcast_payment_status(payment_id):
    from .models import Payment
    p = Payment.objects.filter(id=payment_id).first()
    if not p:
        return
    payload = {
        "type": "payment.status",
        "reference": p.public_reference,
        "status": p.status,
        "method": p.method,
        "amount": str(p.amount),
        "currency": p.currency,
        "receipt_number": p.receipt_number,
    }
    _broadcast(f"payment_{p.public_reference}", payload)
    _broadcast_admin({"type": "admin.event", "event": "payment", "data": payload})

@shared_task
def send_payment_receipt(payment_id):
    from .models import Payment
    from notifications.services import send_donation_receipt
    p = Payment.objects.filter(id=payment_id).first()
    if not p:
        return
    if p.donation:
        send_donation_receipt(p.donation, p)