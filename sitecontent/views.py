import os
import uuid

from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.parsers import (
    MultiPartParser,
    FormParser,
    JSONParser,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SiteContentEdit, SiteContentVersion
from .serializers import (
    SiteContentEditSerializer,
    SiteContentVersionSerializer,
)


def _require_superuser(request):
    return bool(
        request.user
        and request.user.is_authenticated
        and request.user.is_superuser
    )


class SiteContentListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        edits = SiteContentEdit.objects.all()

        data = {
            edit.key: edit.value
            for edit in edits
        }

        last_updated = (
            edits.order_by("-updated_at")
            .values_list("updated_at", flat=True)
            .first()
        )

        return Response(
            {
                "edits": data,
                "count": len(data),
                "last_updated": (
                    last_updated.isoformat()
                    if last_updated
                    else None
                ),
            },
            status=status.HTTP_200_OK,
        )


class SiteContentBulkUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _require_superuser(request):
            return Response(
                {"detail": "Not authorized."},
                status=status.HTTP_403_FORBIDDEN,
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

        updated = 0

        for key, value in edits.items():
            SiteContentEdit.objects.update_or_create(
                key=str(key),
                defaults={
                    "value": value,
                    "updated_by": request.user,
                },
            )
            updated += 1

        deleted = 0

        if deletes:
            keys = [str(key) for key in deletes]

            queryset = SiteContentEdit.objects.filter(
                key__in=keys
            )

            deleted = queryset.count()
            queryset.delete()

        return Response(
            {
                "detail": "Saved.",
                "updated": updated,
                "deleted": deleted,
            },
            status=status.HTTP_200_OK,
        )


class SiteContentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    MAX_BYTES = 10 * 1024 * 1024

    ALLOWED_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".gif",
        ".svg",
    }

    def post(self, request):
        if not _require_superuser(request):
            return Response(
                {"detail": "Not authorized."},
                status=status.HTTP_403_FORBIDDEN,
            )

        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"detail": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if uploaded_file.size > self.MAX_BYTES:
            return Response(
                {
                    "detail": (
                        f"File exceeds "
                        f"{self.MAX_BYTES // (1024 * 1024)} MB."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        extension = os.path.splitext(
            uploaded_file.name or ""
        )[1].lower()

        if extension not in self.ALLOWED_EXTENSIONS:
            return Response(
                {
                    "detail": (
                        "Unsupported file type. "
                        "Use PNG, JPG, WEBP, GIF or SVG."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        filename = f"{uuid.uuid4().hex}{extension}"
        storage_path = f"site-content/{filename}"

        try:
            saved_path = default_storage.save(
                storage_path,
                uploaded_file,
            )

            file_url = default_storage.url(saved_path)

            if file_url.startswith("/"):
                file_url = request.build_absolute_uri(file_url)

            return Response(
                {
                    "url": file_url,
                    "path": saved_path,
                    "filename": filename,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception:
            return Response(
                {
                    "detail": (
                        "Image upload failed. "
                        "Please check the Cloudinary configuration."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SiteContentEditDetailView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [
        JSONParser,
        MultiPartParser,
        FormParser,
    ]

    def get(self, request, key):
        try:
            edit = SiteContentEdit.objects.get(key=key)

        except SiteContentEdit.DoesNotExist:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            SiteContentEditSerializer(edit).data,
            status=status.HTTP_200_OK,
        )

    def put(self, request, key):
        if not _require_superuser(request):
            return Response(
                {"detail": "Not authorized."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if "value" not in request.data:
            return Response(
                {"detail": "value is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        edit, _ = SiteContentEdit.objects.update_or_create(
            key=key,
            defaults={
                "value": request.data.get("value"),
                "updated_by": request.user,
            },
        )

        return Response(
            SiteContentEditSerializer(edit).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, key):
        if not _require_superuser(request):
            return Response(
                {"detail": "Not authorized."},
                status=status.HTTP_403_FORBIDDEN,
            )

        SiteContentEdit.objects.filter(key=key).delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class SiteContentResetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _require_superuser(request):
            return Response(
                {"detail": "Not authorized."},
                status=status.HTTP_403_FORBIDDEN,
            )

        prefix = request.data.get("prefix")

        if prefix:
            queryset = SiteContentEdit.objects.filter(
                key__startswith=str(prefix)
            )

            cleared = queryset.count()
            queryset.delete()

        else:
            cleared = SiteContentEdit.objects.count()
            SiteContentEdit.objects.all().delete()

        return Response(
            {
                "detail": f"Cleared {cleared} edit(s).",
                "cleared": cleared,
            },
            status=status.HTTP_200_OK,
        )


class SiteContentVersionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _require_superuser(request):
            return Response(
                {"detail": "Not authorized."},
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = SiteContentVersion.objects.all()[:50]

        return Response(
            SiteContentVersionSerializer(
                queryset,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        if not _require_superuser(request):
            return Response(
                {"detail": "Not authorized."},
                status=status.HTTP_403_FORBIDDEN,
            )

        note = (
            request.data.get("note") or ""
        ).strip()

        snapshot = {
            edit.key: edit.value
            for edit in SiteContentEdit.objects.all()
        }

        version = SiteContentVersion.objects.create(
            snapshot=snapshot,
            note=note,
            created_by=request.user,
        )

        return Response(
            SiteContentVersionSerializer(version).data,
            status=status.HTTP_201_CREATED,
        )