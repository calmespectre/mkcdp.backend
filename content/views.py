import os
import uuid

from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination
from core.permissions import IsStaffOrSuperuser

from . import services
from .models import ChangeSet, ContentRevision, ContentSnapshot, SiteContent
from .serializers import (
    ChangeSetDetailSerializer,
    ChangeSetSerializer,
    ContentRevisionSerializer,
    ContentSnapshotDetailSerializer,
    ContentSnapshotSerializer,
)

MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/svg+xml",
}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}


def _payload(request):
    data = request.data
    return data if isinstance(data, dict) or hasattr(data, "get") else {}


def _error(detail, code=status.HTTP_400_BAD_REQUEST):
    return Response({"detail": detail}, status=code)


def _changeset_id(result):
    changeset = result.get("changeset")
    return changeset.pk if changeset else None


def _summary(result):
    return {
        "changeset": _changeset_id(result),
        "created": result["created"],
        "updated": result["updated"],
        "deleted": result["deleted"],
        "unchanged": result["unchanged"],
    }


def _paginate(request, queryset, serializer_class):
    paginator = StandardPagination()
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response(serializer_class(page, many=True).data)


class StaffAPIView(APIView):
    permission_classes = [IsStaffOrSuperuser]


class SiteContentRootView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        rows = list(SiteContent.objects.all().order_by("key"))
        edits = {row.key: row.value for row in rows}
        latest = max((row.updated_at for row in rows if row.updated_at), default=None)
        latest_changeset = ChangeSet.objects.order_by("-id").values_list("id", flat=True).first()
        return Response(
            {
                "edits": edits,
                "count": len(edits),
                "last_updated": latest.isoformat() if latest else None,
                "revision": latest_changeset,
            }
        )


class SiteContentItemView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, key):
        row = SiteContent.objects.filter(key=key).first()
        if not row:
            return Response({"key": key, "value": None})
        return Response({"key": row.key, "value": row.value})


class SiteContentBulkView(StaffAPIView):
    def post(self, request):
        data = _payload(request)
        try:
            result = services.apply_changes(
                request.user,
                edits=data.get("edits"),
                deletes=data.get("deletes"),
                action=ChangeSet.ACTION_BULK,
                note=data.get("note") or "",
            )
        except services.ContentError as exc:
            return _error(exc.detail, exc.status_code)
        return Response({"ok": True, **_summary(result)})


class SiteContentResetView(StaffAPIView):
    def post(self, request):
        data = _payload(request)
        prefix = data.get("prefix") or ""
        if not isinstance(prefix, str):
            return _error("prefix must be a string.")
        try:
            result = services.reset_content(request.user, prefix=prefix, note=data.get("note") or "")
        except services.ContentError as exc:
            return _error(exc.detail, exc.status_code)
        return Response(
            {
                "ok": True,
                "prefix": prefix or None,
                "cleared": result["cleared"],
                "changeset": _changeset_id(result),
            }
        )


class SiteContentUploadView(StaffAPIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get("file") or request.FILES.get("image")
        if not file:
            return _error("No file provided.")
        if file.size > MAX_IMAGE_BYTES:
            return _error("File exceeds 10 MB.")
        content_type = (file.content_type or "").lower()
        if content_type and content_type not in ALLOWED_IMAGE_TYPES:
            return _error("Unsupported image type.")
        ext = os.path.splitext(file.name or "")[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            return _error("Unsupported file extension. Use PNG, JPG, WEBP, GIF or SVG.")
        name = f"site-content/{timezone.now().strftime('%Y/%m')}/{uuid.uuid4().hex}{ext}"
        try:
            saved_path = default_storage.save(name, file)
            url = default_storage.url(saved_path)
        except Exception:
            return _error("Image upload failed.", status.HTTP_500_INTERNAL_SERVER_ERROR)
        if url.startswith("/"):
            url = request.build_absolute_uri(url)
        return Response({"url": url, "path": saved_path}, status=status.HTTP_201_CREATED)


class RevisionListView(StaffAPIView):
    def get(self, request):
        qs = ContentRevision.objects.select_related("actor").all()
        params = request.query_params
        key = params.get("key")
        prefix = params.get("prefix")
        action = params.get("action")
        actor = params.get("actor")
        changeset = params.get("changeset")
        since = params.get("since")
        until = params.get("until")
        if key:
            qs = qs.filter(key=key)
        if prefix:
            qs = qs.filter(key__startswith=prefix)
        if action:
            qs = qs.filter(action=action)
        if actor:
            qs = qs.filter(actor_id=actor)
        if changeset and changeset.isdigit():
            qs = qs.filter(changeset_id=int(changeset))
        if since:
            qs = qs.filter(created_at__gte=since)
        if until:
            qs = qs.filter(created_at__lte=until)
        return _paginate(request, qs, ContentRevisionSerializer)


class RevisionDetailView(StaffAPIView):
    def get(self, request, pk):
        revision = get_object_or_404(ContentRevision.objects.select_related("actor"), pk=pk)
        return Response(ContentRevisionSerializer(revision).data)


class RevisionRestoreView(StaffAPIView):
    def post(self, request, pk):
        revision = get_object_or_404(ContentRevision, pk=pk)
        data = _payload(request)
        try:
            result = services.restore_revision(
                request.user,
                revision,
                target=data.get("target") or "before",
                note=data.get("note") or "",
            )
        except services.ContentError as exc:
            return _error(exc.detail, exc.status_code)
        return Response({"ok": True, **_summary(result)})


class KeyHistoryView(StaffAPIView):
    def get(self, request, key):
        qs = ContentRevision.objects.select_related("actor").filter(key=key)
        return _paginate(request, qs, ContentRevisionSerializer)


class ChangeSetListView(StaffAPIView):
    def get(self, request):
        qs = ChangeSet.objects.select_related("actor").all()
        params = request.query_params
        action = params.get("action")
        actor = params.get("actor")
        if action:
            qs = qs.filter(action=action)
        if actor:
            qs = qs.filter(actor_id=actor)
        return _paginate(request, qs, ChangeSetSerializer)


class ChangeSetDetailView(StaffAPIView):
    def get(self, request, pk):
        changeset = get_object_or_404(
            ChangeSet.objects.select_related("actor").prefetch_related("revisions__actor"),
            pk=pk,
        )
        return Response(ChangeSetDetailSerializer(changeset).data)


class ChangeSetRevertView(StaffAPIView):
    def post(self, request, pk):
        changeset = get_object_or_404(ChangeSet, pk=pk)
        data = _payload(request)
        try:
            result = services.revert_changeset(request.user, changeset, note=data.get("note") or "")
        except services.ContentError as exc:
            return _error(exc.detail, exc.status_code)
        return Response({"ok": True, **_summary(result)})


class SnapshotListView(StaffAPIView):
    def get(self, request):
        qs = ContentSnapshot.objects.select_related("created_by").all()
        return _paginate(request, qs, ContentSnapshotSerializer)

    def post(self, request):
        data = _payload(request)
        try:
            snapshot = services.create_snapshot(
                request.user,
                data.get("name") or "",
                note=data.get("note") or "",
            )
        except services.ContentError as exc:
            return _error(exc.detail, exc.status_code)
        return Response(ContentSnapshotSerializer(snapshot).data, status=status.HTTP_201_CREATED)


class SnapshotDetailView(StaffAPIView):
    def get(self, request, pk):
        snapshot = get_object_or_404(ContentSnapshot.objects.select_related("created_by"), pk=pk)
        return Response(ContentSnapshotDetailSerializer(snapshot).data)

    def delete(self, request, pk):
        snapshot = get_object_or_404(ContentSnapshot, pk=pk)
        snapshot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SnapshotRestoreView(StaffAPIView):
    def post(self, request, pk):
        snapshot = get_object_or_404(ContentSnapshot, pk=pk)
        data = _payload(request)
        backup = data.get("backup", True)
        if isinstance(backup, str):
            backup = backup.lower() not in ("0", "false", "no")
        try:
            result = services.restore_snapshot(
                request.user,
                snapshot,
                note=data.get("note") or "",
                backup=bool(backup),
            )
        except services.ContentError as exc:
            return _error(exc.detail, exc.status_code)
        backup_snapshot = result.get("backup")
        return Response(
            {
                "ok": True,
                **_summary(result),
                "backup_snapshot": backup_snapshot.pk if backup_snapshot else None,
            }
        )


site_content_root = SiteContentRootView.as_view()
site_content_item = SiteContentItemView.as_view()
site_content_bulk = SiteContentBulkView.as_view()
site_content_reset = SiteContentResetView.as_view()
site_content_upload = SiteContentUploadView.as_view()
