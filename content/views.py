from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import SiteContent, ContentRevision
from .serializers import SiteContentSerializer, ContentRevisionSerializer
from core.permissions import IsStaffOrSuperuser


class SiteContentViewSet(viewsets.ModelViewSet):
    queryset = SiteContent.objects.all()
    serializer_class = SiteContentSerializer
    lookup_field = "key"
    permission_classes = [IsStaffOrSuperuser]
    search_fields = ["key", "description"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return super().get_permissions()

    def perform_update(self, serializer):
        instance = self.get_object()
        before = instance.value
        obj = serializer.save(updated_by=self.request.user)
        ContentRevision.objects.create(
            key=obj.key, before=before, after=obj.value, actor=self.request.user
        )

    def perform_create(self, serializer):
        obj = serializer.save(updated_by=self.request.user)
        ContentRevision.objects.create(
            key=obj.key, before=None, after=obj.value, actor=self.request.user
        )


class ContentRevisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContentRevision.objects.select_related("actor")
    serializer_class = ContentRevisionSerializer
    permission_classes = [IsStaffOrSuperuser]
    filterset_fields = ["key"]


@api_view(["GET", "OPTIONS", "HEAD"])
@permission_classes([AllowAny])
def bulk_content(request):
    prefix = request.query_params.get("prefix", "")
    qs = SiteContent.objects.all()
    if prefix:
        qs = qs.filter(key__startswith=prefix)
    return Response({"success": True, "data": {c.key: c.value for c in qs}})


@api_view(["POST", "OPTIONS"])
@permission_classes([IsStaffOrSuperuser])
def bulk_update_content(request):
    payload = request.data or {}
    if not isinstance(payload, dict):
        return Response(
            {"success": False, "errors": {"detail": ["Expected an object of key → value."]}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    updated = []
    for key, value in payload.items():
        obj, created = SiteContent.objects.get_or_create(
            key=key, defaults={"value": value, "updated_by": request.user}
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
        updated.append(key)
    return Response({"success": True, "data": {"updated": updated}})
