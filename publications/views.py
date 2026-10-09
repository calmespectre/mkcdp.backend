from rest_framework import viewsets, filters, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Publication
from .serializers import PublicationSerializer
from core.permissions import IsStaffOrSuperuser


class PublicationViewSet(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    permission_classes = [IsStaffOrSuperuser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "year", "published", "file_type"]
    search_fields = ["title", "description"]
    ordering_fields = ["year", "created_at", "title"]
    parser_classes = [
        parsers.MultiPartParser,
        parsers.FormParser,
        parsers.JSONParser,
    ]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsStaffOrSuperuser()]

    def get_queryset(self):
        qs = Publication.objects.all()
        user = self.request.user
        is_staff = bool(
            user
            and user.is_authenticated
            and (user.is_staff or user.is_superuser)
        )
        if not is_staff:
            qs = qs.filter(published=True)
        return qs

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(uploaded_by=user)

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(qs, many=True)

        categories = [
            {"id": cid, "label": label}
            for cid, label in Publication.CATEGORIES
        ]
        years = list(
            Publication.objects.filter(published=True)
            .exclude(year__isnull=True)
            .values_list("year", flat=True)
            .distinct()
            .order_by("-year")
        )

        return Response(
            {
                "results": serializer.data,
                "categories": categories,
                "years": years,
            }
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)