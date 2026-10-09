from django.conf import settings
from .base import PaymentProvider
from core.utils import reference

class BankProvider(PaymentProvider):
    name = "bank"
    method = "bank"

    def initiate(self, payment):
        ref = reference("BT")
        payment.bank_reference = ref
        payment.status = "pending_verification"
        payment.provider_response = {
            "instructions": {
                "bank_name": settings.BANK["NAME"],
                "account_name": settings.BANK["ACCOUNT_NAME"],
                "account_number": settings.BANK["ACCOUNT_NUMBER"],
                "branch": settings.BANK["BRANCH"],
                "swift": settings.BANK["SWIFT"],
                "reference": ref,
                "amount_kes": str(payment.amount_kes),
                "note": "Include the reference above in your transfer description.",
            }
        }
        payment.save()
        return payment

    def handle_webhook(self, payload):
        return None