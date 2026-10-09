from celery import shared_task
from .services import send_email


@shared_task
def send_verification_code_email(user_id, code, purpose):
    from accounts.models import User
    user = User.objects.filter(id=user_id).first()
    if not user:
        return
    subject = "Your MKCDP verification code" if purpose == "signin" else "Confirm your MKCDP account"
    context = {"user": user, "code": code, "purpose": purpose, "expires_minutes": 10}
    send_email(subject, "verification_code", context, user.email)


@shared_task
def send_donation_receipt_email(donation_id, payment_id):
    from donations.models import Donation
    from payments.models import Payment
    from .services import send_donation_receipt
    d = Donation.objects.filter(id=donation_id).first()
    p = Payment.objects.filter(id=payment_id).first()
    if d and p:
        send_donation_receipt(d, p)


@shared_task
def send_bank_verified_email(payment_id):
    from payments.models import Payment
    p = Payment.objects.filter(id=payment_id).first()
    if not p:
        return
    email = p.donation.email if p.donation else (p.gift_order.email if p.gift_order else "")
    send_email(
        f"MKCDP bank transfer verified — {p.public_reference}",
        "generic",
        {"message": "Your bank transfer has been verified. Thank you."},
        email,
    )


@shared_task
def send_volunteer_confirmation(application_id):
    from volunteers.models import VolunteerApplication
    a = VolunteerApplication.objects.filter(id=application_id).first()
    if not a or not a.email:
        return
    send_email(
        "We received your volunteer application",
        "generic",
        {"message": f"Thank you for applying for {a.opportunity.title}."},
        a.email,
    )


@shared_task
def send_partnership_confirmation(enquiry_id):
    from partnerships.models import PartnershipEnquiry
    e = PartnershipEnquiry.objects.filter(id=enquiry_id).first()
    if not e:
        return
    send_email(
        "We received your partnership enquiry",
        "generic",
        {"message": f"Thank you, {e.contact_name}. We'll be in touch."},
        e.email,
    )


@shared_task
def send_safeguarding_ack(report_id):
    from safeguarding.models import SafeguardingReport
    r = SafeguardingReport.objects.filter(id=report_id).first()
    if not r or not r.email:
        return
    send_email(
        "Your safeguarding report was received",
        "generic",
        {"message": f"Reference {r.reference}. We take this seriously."},
        r.email,
    )