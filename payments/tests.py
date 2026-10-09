from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from donations.models import Donation
from payments.models import Payment

class BankVerificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.donation = Donation.objects.create(
            reference="DON-TEST", first_name="A", last_name="B",
            email="a@example.com", phone="+254712345678",
            amount_kes=Decimal("1500"), requested_amount=Decimal("1500"),
            requested_currency="KES", exchange_rate=Decimal("1"),
            payment_method="bank", status="pending",
        )
        self.payment = Payment.objects.create(
            public_reference="PAY-TEST", donation=self.donation,
            provider="bank", method="bank", currency="KES",
            amount=Decimal("1500"), amount_kes=Decimal("1500"),
            status="pending_verification",
        )

    def test_staff_verification_marks_complete(self):
        from accounts.models import User
        staff = User.objects.create_user("staff@example.com", "pw12345678", is_staff=True)
        self.client.force_authenticate(staff)
        r = self.client.post(f"/api/payments/bank/{self.payment.public_reference}/verify/", {"approve": True}, format="json")
        self.assertEqual(r.status_code, 200)
        self.payment.refresh_from_db()
        self.donation.refresh_from_db()
        self.assertEqual(self.payment.status, "completed")
        self.assertEqual(self.donation.status, "completed")

    def test_public_cannot_verify(self):
        r = self.client.post(f"/api/payments/bank/{self.payment.public_reference}/verify/", {"approve": True}, format="json")
        self.assertIn(r.status_code, (401, 403))