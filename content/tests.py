from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import ChangeSet, ContentRevision, ContentSnapshot, SiteContent

User = get_user_model()


class ContentBackendTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(email="staff@example.com", password="pass12345", is_staff=True)
        self.visitor = User.objects.create_user(email="visitor@example.com", password="pass12345")
        self.client = APIClient()
        self.client.force_authenticate(self.staff)
        self.anon = APIClient()

    def bulk(self, edits=None, deletes=None):
        return self.client.post("/api/site-content/bulk/", {"edits": edits or {}, "deletes": deletes or []}, format="json")

    def test_public_read_and_protected_write(self):
        self.bulk({"a.b": "one"})
        response = self.anon.get("/api/site-content/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["edits"], {"a.b": "one"})
        self.assertIn(self.anon.post("/api/site-content/bulk/", {"edits": {"x": 1}}, format="json").status_code, (401, 403))
        self.client.force_authenticate(self.visitor)
        self.assertEqual(self.bulk({"x": 1}).status_code, 403)

    def test_bulk_creates_updates_deletes_and_records_history(self):
        first = self.bulk({"a": "one", "b": "two"})
        self.assertEqual(first.data["created"], 2)
        second = self.bulk({"a": "uno"}, ["b"])
        self.assertEqual(second.data["updated"], 1)
        self.assertEqual(second.data["deleted"], 1)
        self.assertEqual(SiteContent.objects.count(), 1)
        self.assertEqual(ChangeSet.objects.count(), 2)
        revisions = ContentRevision.objects.filter(key="a").order_by("version")
        self.assertEqual([r.version for r in revisions], [1, 2])
        self.assertEqual(revisions[1].before, "one")
        self.assertEqual(revisions[1].after, "uno")

    def test_unchanged_values_create_no_history(self):
        self.bulk({"a": "one"})
        response = self.bulk({"a": "one"})
        self.assertIsNone(response.data["changeset"])
        self.assertEqual(response.data["unchanged"], 1)
        self.assertEqual(ChangeSet.objects.count(), 1)

    def test_invalid_payloads_rejected(self):
        self.assertEqual(self.client.post("/api/site-content/bulk/", {"edits": []}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/site-content/bulk/", {"deletes": "x"}, format="json").status_code, 400)
        self.assertEqual(self.bulk({"": "v"}).status_code, 400)
        self.assertEqual(SiteContent.objects.count(), 0)

    def test_restore_revision(self):
        self.bulk({"a": "one"})
        self.bulk({"a": "two"})
        revision = ContentRevision.objects.filter(key="a", version=2).first()
        response = self.client.post(f"/api/site-content/history/{revision.pk}/restore/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SiteContent.objects.get(key="a").value, "one")
        self.assertEqual(ContentRevision.objects.filter(key="a").count(), 3)

    def test_restore_created_revision_deletes_key(self):
        self.bulk({"a": "one"})
        revision = ContentRevision.objects.get(key="a")
        self.client.post(f"/api/site-content/history/{revision.pk}/restore/", {}, format="json")
        self.assertFalse(SiteContent.objects.filter(key="a").exists())

    def test_revert_changeset(self):
        self.bulk({"a": "one", "b": "two"})
        result = self.bulk({"a": "uno", "c": "three"}, ["b"])
        response = self.client.post(f"/api/site-content/changesets/{result.data['changeset']}/revert/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        values = {row.key: row.value for row in SiteContent.objects.all()}
        self.assertEqual(values, {"a": "one", "b": "two"})

    def test_reset_with_prefix_is_recorded(self):
        self.bulk({"home.title": "x", "home.sub": "y", "about.title": "z"})
        response = self.client.post("/api/site-content/reset/", {"prefix": "home."}, format="json")
        self.assertEqual(response.data["cleared"], 2)
        self.assertEqual(SiteContent.objects.count(), 1)
        self.assertEqual(ChangeSet.objects.filter(action=ChangeSet.ACTION_RESET).count(), 1)

    def test_snapshot_create_and_restore(self):
        self.bulk({"a": "one", "b": "two"})
        created = self.client.post("/api/site-content/snapshots/", {"name": "v1"}, format="json")
        self.assertEqual(created.status_code, 201)
        snapshot_id = created.data["id"]
        self.bulk({"a": "changed", "c": "new"}, ["b"])
        response = self.client.post(f"/api/site-content/snapshots/{snapshot_id}/restore/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        values = {row.key: row.value for row in SiteContent.objects.all()}
        self.assertEqual(values, {"a": "one", "b": "two"})
        self.assertEqual(ContentSnapshot.objects.count(), 2)

    def test_history_listing_filters(self):
        self.bulk({"a": "one", "b": "two"})
        self.bulk({"a": "uno"})
        response = self.client.get("/api/site-content/history/?key=a")
        self.assertEqual(response.data["count"], 2)
        response = self.client.get("/api/site-content/key/a/history/")
        self.assertEqual(response.data["count"], 2)
        response = self.client.get("/api/site-content/changesets/")
        self.assertEqual(response.data["count"], 2)
