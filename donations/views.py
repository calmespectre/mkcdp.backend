from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from .models import Donation
from .serializers import DonationSerializer, DonationCreateSerializer
from .services import create_donation
from core.permissions import IsStaffOrSuperuser
from core.utils import client_ip
from core.models import AuditLog

class DonationCreateView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payment"

    def post(self, request):
        serializer = DonationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user if request.user.is_authenticated else None
        donation, payment = create_donation(data=serializer.validated_data, user=user)
        AuditLog.objects.create(
            actor=user,
            action="payment_init",
            entity_type="donation",
            entity_id=str(donation.id),
            after={"reference": donation.reference, "method": donation.payment_method},
            ip_address=client_ip(request),
            request_id=getattr(request, "request_id", ""),
        )
        from payments.serializers import PaymentSerializer
        return Response({
            "success": True,
            "data": {
                "donation": DonationSerializer(donation).data,
                "payment": PaymentSerializer(payment).data,
                "next_action": payment.next_action(),
            },
        }, status=201)

class DonationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DonationSerializer
    permission_classes = [IsStaffOrSuperuser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "frequency", "payment_method", "requested_currency"]
    search_fields = ["reference", "email", "first_name", "last_name", "phone"]
    queryset = Donation.objects.all().order_by("-created_at")

class MyDonationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Donation.objects.filter(donor=request.user).order_by("-created_at")
        return Response({"success": True, "data": DonationSerializer(qs, many=True).data})