from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from volunteers.models import Opportunity, VolunteerApplication

class VolunteerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.opp = Opportunity.objects.create(
            code="VOL-1", org="MKCDP", title="Reader", location="Nairobi",
            commitment="4 hrs/wk", description="Read with children.",
        )

    def test_public_can_apply(self):
        r = self.client.post("/api/volunteers/applications/submit/", {
            "opportunity_id": str(self.opp.id),
            "full_name": "Jane Doe",
            "phone": "+254712345678",
            "email": "jane@example.com",
            "availability": "weekends",
            "note": "I love reading.",
        }, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(VolunteerApplication.objects.count(), 1)

    def test_only_staff_create_opportunity(self):
        anon = self.client.post("/api/volunteers/opportunities/", {"org": "X", "title": "Y"}, format="json")
        self.assertIn(anon.status_code, (401, 403))
        staff = User.objects.create_user("s@example.com", "pw12345678", is_staff=True)
        self.client.force_authenticate(staff)
        r = self.client.post("/api/volunteers/opportunities/", {
            "code": "VOL-2", "org": "X", "title": "Y", "location": "Z",
            "commitment": "any", "description": "desc",
        }, format="json")
        self.assertEqual(r.status_code, 201)