from django.test import TestCase
from rest_framework.test import APIClient

class SafeguardingTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_anonymous_submission(self):
        r = self.client.post("/api/safeguarding/submit/", {
            "reporter_type": "Community member",
            "anonymous": True,
            "relationship": "Neighbour",
            "location": "Kampala",
            "concerns": ["neglect"],
            "urgency": "urgent",
            "description": "This is a detailed description of what happened.",
            "contact_preference": "none",
        }, format="json")
        self.assertEqual(r.status_code, 201)

    def test_unauthorized_cannot_list(self):
        r = self.client.get("/api/safeguarding/reports/")
        self.assertIn(r.status_code, (401, 403))