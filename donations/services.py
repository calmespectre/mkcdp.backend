from django.db import transaction
from django.utils import timezone
from .models import Donation
from core.utils import reference

def create_donation(*, data, user=None):
    from payments.services import initiate_payment
    with transaction.atomic():
        if data.get("idempotency_key"):
            existing = Donation.objects.filter(idempotency_key=data["idempotency_key"]).first()
            if existing:
                return existing, existing.payments.order_by("-created_at").first()
        donation = Donation.objects.create(
            reference=reference("DON"),
            donor=user if (user and user.is_authenticated) else None,
            first_name=data["first_name"].strip(),
            last_name=data["last_name"].strip(),
            email=data["email"].lower().strip(),
            phone=data["phone"].strip(),
            amount_kes=data["amount_kes"],
            requested_amount=data["requested_amount"],
            requested_currency=data["requested_currency"],
            exchange_rate=data["exchange_rate"],
            frequency=data["frequency"],
            payment_method=data["payment_method"],
            impact_note=data.get("impact_note", ""),
            idempotency_key=data.get("idempotency_key", ""),
            status="pending",
        )
    payment = initiate_payment(donation=donation, method=data["payment_method"])
    return donation, payment