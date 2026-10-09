from rest_framework import viewsets, filters, parsers
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Beneficiary, Sponsorship
from .serializers import BeneficiarySerializer, SponsorshipSerializer
from core.permissions import IsStaffOrSuperuser


class BeneficiaryViewSet(viewsets.ModelViewSet):
    serializer_class = BeneficiarySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "gender", "published"]
    search_fields = ["name", "location", "grade"]
    ordering_fields = ["display_order", "created_at", "monthly_usd"]
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        qs = Beneficiary.objects.all()
        user = self.request.user
        if not (user.is_authenticated and (user.is_staff or user.is_superuser)):
            qs = qs.filter(published=True)
        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsStaffOrSuperuser()]


class SponsorshipViewSet(viewsets.ModelViewSet):
    queryset = Sponsorship.objects.all().order_by("-created_at")
    serializer_class = SponsorshipSerializer
    permission_classes = [IsStaffOrSuperuser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["beneficiary", "active"]