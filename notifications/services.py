import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

def send_email(subject, template, context, to):
    if not to:
        return
    try:
        html = render_to_string(f"emails/{template}.html", context)
        msg = EmailMultiAlternatives(subject, html, settings.DEFAULT_FROM_EMAIL, [to] if isinstance(to, str) else to)
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)
    except Exception:
        logger.exception("Email send failed to %s", to)

def send_donation_receipt(donation, payment):
    context = {
        "donation": donation,
        "payment": payment,
        "org_name": "MKCDP",
        "frontend_url": settings.FRONTEND_URL,
    }
    send_email(f"Your MKCDP donation receipt — {donation.reference}", "donation_receipt", context, donation.email)

def send_bank_instructions_email(payment):
    donation = payment.donation
    email = donation.email if donation else payment.gift_order.email
    context = {"payment": payment, "instructions": payment.provider_response.get("instructions", {})}
    send_email(f"MKCDP bank transfer instructions — {payment.public_reference}", "bank_instructions", context, email)