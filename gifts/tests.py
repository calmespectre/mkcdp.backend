from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from gifts.models import GiftNeed, GiftOrder

class GiftOrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.need = GiftNeed.objects.create(
            slug="n1", title="Books", price_kes=Decimal("500"),
            child_name="Amina", child_grade="P2", child_location="Kampala",
        )

    def test_order_totals_use_server_price(self):
        r = self.client.post("/api/gifts/orders/create/", {
            "name": "Test", "email": "t@example.com", "currency": "KES",
            "payment_method": "bank",
            "items": [{"id": str(self.need.id), "quantity": 2}],
        }, format="json")
        self.assertEqual(r.status_code, 201)
        order = GiftOrder.objects.first()
        self.assertEqual(order.total_kes, Decimal("1000.00"))

    def test_rejects_price_tampering(self):
        r = self.client.post("/api/gifts/orders/create/", {
            "name": "Test", "email": "t@example.com", "currency": "KES",
            "payment_method": "bank",
            "items": [{"id": str(self.need.id), "quantity": 1, "price": 1}],
        }, format="json")
        self.assertEqual(r.status_code, 201)
        order = GiftOrder.objects.first()
        self.assertEqual(order.total_kes, Decimal("500.00"))