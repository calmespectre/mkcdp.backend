import os
import uuid
from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import SiteContent, ContentRevision


MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"}


def _is_staff(user):
    return bool(
        user
        and user.is_authenticated
        and (user.is_staff or user.is_superuser)
    )


@api_view(["GET", "OPTIONS"])
@permission_classes([AllowAny])
def site_content_root(request):
    qs = SiteContent.objects.all().order_by("key")
    edits = {row.key: row.value for row in qs}

    last_updated = None
    latest = qs.order_by("-updated_at").first()
    if latest and latest.updated_at:
        last_updated = latest.updated_at.isoformat()

    return Response(
        {
            "edits": edits,
            "last_updated": last_updated,
        }
    )


@api_view(["POST", "OPTIONS"])
@permission_classes([AllowAny])
def site_content_bulk(request):
    if not _is_staff(request.user):
        return Response(
            {"detail": "Authentication required."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    payload = request.data or {}
    edits = payload.get("edits") or {}
    deletes = payload.get("deletes") or []

    if not isinstance(edits, dict):
        return Response(
            {"detail": "edits must be an object."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not isinstance(deletes, list):
        return Response(
            {"detail": "deletes must be an array."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    for key, value in edits.items():
        obj, created = SiteContent.objects.get_or_create(
            key=key,
            defaults={"value": value, "updated_by": request.user},
        )
        if created:
            ContentRevision.objects.create(
                key=key, before=None, after=value, actor=request.user
            )
        else:
            before = obj.value
            obj.value = value
            obj.updated_by = request.user
            obj.save()
            ContentRevision.objects.create(
                key=key, before=before, after=value, actor=request.user
            )

    if deletes:
        for key in deletes:
            obj = SiteContent.objects.filter(key=key).first()
            if obj:
                before = obj.value
                obj.delete()
                ContentRevision.objects.create(
                    key=key, before=before, after=None, actor=request.user
                )

    return Response({"ok": True})


@api_view(["POST", "OPTIONS"])
@permission_classes([AllowAny])
def site_content_reset(request):
    if not _is_staff(request.user):
        return Response(
            {"detail": "Authentication required."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    prefix = (request.data or {}).get("prefix") or ""
    qs = SiteContent.objects.all()
    if prefix:
        qs = qs.filter(key__startswith=prefix)

    for obj in qs:
        ContentRevision.objects.create(
            key=obj.key, before=obj.value, after=None, actor=request.user
        )
    qs.delete()

    return Response({"ok": True, "prefix": prefix or None})


@api_view(["POST", "OPTIONS"])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def site_content_upload(request):
    if not _is_staff(request.user):
        return Response(
            {"detail": "Authentication required."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    file = request.FILES.get("file") or request.FILES.get("image")
    if not file:
        return Response(
            {"detail": "No file provided."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if file.size > MAX_IMAGE_BYTES:
        return Response(
            {"detail": "File exceeds 10 MB."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ctype = (file.content_type or "").lower()
    if ctype and ctype not in ALLOWED_IMAGE_TYPES:
        return Response(
            {"detail": "Unsupported image type."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ext = os.path.splitext(file.name or "")[1].lower() or ".bin"
    name = f"site-content/{timezone.now().strftime('%Y/%m')}/{uuid.uuid4().hex}{ext}"
    saved_path = default_storage.save(name, file)
    url = default_storage.url(saved_path)

    if url.startswith("/"):
        url = request.build_absolute_uri(url)

    return Response({"url": url}, status=status.HTTP_201_CREATED)


@api_view(["GET", "OPTIONS", "HEAD"])
@permission_classes([AllowAny])
def site_content_item(request, key):
    obj = SiteContent.objects.filter(key=key).first()
    if not obj:
        return Response({"key": key, "value": None})
    return Response({"key": obj.key, "value": obj.value})