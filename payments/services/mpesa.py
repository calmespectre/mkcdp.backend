import base64
import logging
from datetime import datetime
from decimal import Decimal
import requests
from django.conf import settings
from django.utils import timezone
from .base import PaymentProvider
from core.utils import normalize_phone, reference

logger = logging.getLogger(__name__)

class MpesaProvider(PaymentProvider):
    name = "mpesa"
    method = "mpesa"

    def _base_url(self):
        return "https://sandbox.safaricom.co.ke" if settings.MPESA["ENVIRONMENT"] == "sandbox" else "https://api.safaricom.co.ke"

    def _token(self):
        url = f"{self._base_url()}/oauth/v1/generate?grant_type=client_credentials"
        r = requests.get(url, auth=(settings.MPESA["CONSUMER_KEY"], settings.MPESA["CONSUMER_SECRET"]), timeout=20)
        r.raise_for_status()
        return r.json()["access_token"]

    def _password(self, timestamp):
        raw = f"{settings.MPESA['SHORTCODE']}{settings.MPESA['PASSKEY']}{timestamp}"
        return base64.b64encode(raw.encode()).decode()

    def initiate(self, payment):
        token = self._token()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        phone = normalize_phone(payment.donation.phone if payment.donation else payment.gift_order.phone)
        amount = int(payment.amount_kes)
        if amount < 1:
            raise ValueError("M-Pesa amount must be at least 1 KES.")
        payload = {
            "BusinessShortCode": settings.MPESA["SHORTCODE"],
            "Password": self._password(timestamp),
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": settings.MPESA["SHORTCODE"],
            "PhoneNumber": phone,
            "CallBackURL": settings.MPESA["CALLBACK_URL"],
            "AccountReference": payment.public_reference[:12],
            "TransactionDesc": f"MKCDP {payment.public_reference}",
        }
        url = f"{self._base_url()}/mpesa/stkpush/v1/processrequest"
        r = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        data = r.json()
        logger.info("M-Pesa STK push response ref=%s data=%s", payment.public_reference, data)
        payment.provider_response = data
        if data.get("ResponseCode") == "0":
            payment.provider_checkout_id = data.get("CheckoutRequestID", "")
            payment.provider_transaction_id = data.get("MerchantRequestID", "")
            payment.status = "processing"
        else:
            payment.status = "failed"
            payment.failure_reason = data.get("errorMessage") or data.get("ResponseDescription", "STK push failed")
        payment.save()
        return payment

    def handle_webhook(self, payload):
        from payments.models import Payment
        body = (payload or {}).get("Body", {}).get("stkCallback", {})
        checkout_id = body.get("CheckoutRequestID")
        result_code = str(body.get("ResultCode"))
        payment = Payment.objects.filter(provider_checkout_id=checkout_id).first()
        if not payment:
            logger.warning("M-Pesa callback for unknown checkout id %s", checkout_id)
            return None
        if payment.status in ("completed", "refunded"):
            return payment
        payment.provider_response = {**(payment.provider_response or {}), "callback": body}
        if result_code == "0":
            items = {i.get("Name"): i.get("Value") for i in body.get("CallbackMetadata", {}).get("Item", [])}
            payment.provider_transaction_id = str(items.get("MpesaReceiptNumber", payment.provider_transaction_id))
            payment.paid_at = timezone.now()
            payment.status = "completed"
        else:
            payment.status = "failed"
            payment.failure_reason = body.get("ResultDesc", "M-Pesa failure")
        payment.save()
        return payment