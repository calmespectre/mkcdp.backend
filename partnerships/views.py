from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from .models import PartnershipEnquiry
from .serializers import PartnershipEnquirySerializer
from core.permissions import IsStaffOrSuperuser

class PartnershipEnquiryViewSet(viewsets.ModelViewSet):
    queryset = PartnershipEnquiry.objects.all().order_by("-created_at")
    serializer_class = PartnershipEnquirySerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "anon"

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsStaffOrSuperuser()]

    def perform_create(self, serializer):
        obj = serializer.save()
        from payments.tasks import _broadcast_admin
        _broadcast_admin({"type": "admin.event", "event": "partnership_enquiry", "data": {"id": str(obj.id), "organisation": obj.organisation}})
        from notifications.tasks import send_partnership_confirmation
        send_partnership_confirmation.delay(str(obj.id))