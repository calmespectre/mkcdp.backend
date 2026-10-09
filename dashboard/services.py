from datetime import date
from decimal import Decimal
from django.db.models import Sum, Count, Q
from django.utils import timezone
from donations.models import Donation
from payments.models import Payment
from gifts.models import GiftOrder
from volunteers.models import VolunteerApplication
from partnerships.models import PartnershipEnquiry
from safeguarding.models import SafeguardingReport
from beneficiaries.models import Beneficiary

def month_start():
    today = timezone.now().date()
    return today.replace(day=1)

def stats():
    completed = Donation.objects.filter(status="completed")
    total_raised = completed.aggregate(s=Sum("amount_kes"))["s"] or Decimal("0")
    month_raised = completed.filter(created_at__gte=month_start()).aggregate(s=Sum("amount_kes"))["s"] or Decimal("0")
    by_method = {r["payment_method"]: r["s"] or Decimal("0") for r in completed.values("payment_method").annotate(s=Sum("amount_kes"))}
    return {
        "donations": {
            "total": Donation.objects.count(),
            "completed": completed.count(),
            "pending": Donation.objects.filter(status="pending").count(),
            "processing": Donation.objects.filter(status="processing").count(),
            "failed": Donation.objects.filter(status="failed").count(),
            "monthly_recurring": Donation.objects.filter(frequency="monthly", status="completed").count(),
            "total_raised_kes": str(total_raised),
            "month_raised_kes": str(month_raised),
            "by_method": {k: str(v) for k, v in by_method.items()},
        },
        "bank_transfers": {
            "pending": Payment.objects.filter(method="bank", status="pending_verification").count(),
        },
        "gift_orders": {
            "total": GiftOrder.objects.count(),
            "paid": GiftOrder.objects.filter(status="paid").count(),
        },
        "volunteers": {
            "opportunities": sum(1 for _ in VolunteerApplication.objects.values("opportunity").distinct()),
            "applications": VolunteerApplication.objects.count(),
            "new_applications": VolunteerApplication.objects.filter(status="new").count(),
        },
        "partnerships": {
            "total": PartnershipEnquiry.objects.count(),
            "new": PartnershipEnquiry.objects.filter(status="new").count(),
        },
        "safeguarding": {
            "total": SafeguardingReport.objects.count(),
            "open": SafeguardingReport.objects.exclude(status__in=["resolved", "closed"]).count(),
            "immediate": SafeguardingReport.objects.filter(urgency="immediate").exclude(status__in=["resolved", "closed"]).count(),
        },
        "beneficiaries": {
            "total": Beneficiary.objects.count(),
            "available": Beneficiary.objects.filter(status="Available", published=True).count(),
            "sponsored": Beneficiary.objects.filter(status="Sponsored").count(),
        },
    }