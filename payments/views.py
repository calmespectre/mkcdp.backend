from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import Payment
from .serializers import PaymentSerializer, BankVerifySerializer
from core.permissions import IsStaffOrSuperuser
from core.models import AuditLog
from core.utils import client_ip
from .services import mark_payment_completed
from notifications.tasks import send_bank_verified_email

class PaymentStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, reference):
        payment = Payment.objects.filter(public_reference=reference).first()
        if not payment:
            return Response({"success": False, "errors": {"detail": ["Payment not found."]}}, status=404)
        return Response({"success": True, "data": PaymentSerializer(payment).data})

class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.all().order_by("-created_at")
    serializer_class = PaymentSerializer
    permission_classes = [IsStaffOrSuperuser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "method", "provider"]
    search_fields = ["public_reference", "provider_transaction_id", "provider_checkout_id"]

class BankVerifyView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def post(self, request, reference):
        payment = Payment.objects.select_for_update().filter(public_reference=reference, method="bank").first()
        if not payment:
            return Response({"success": False, "errors": {"detail": ["Bank payment not found."]}}, status=404)
        if payment.status == "completed":
            return Response({"success": False, "errors": {"detail": ["Already verified."]}}, status=400)
        serializer = BankVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approve = serializer.validated_data["approve"]
        before = {"status": payment.status}
        if approve:
            payment.bank_verified_by = request.user
            payment.bank_verified_at = timezone.now()
            payment.bank_notes = serializer.validated_data.get("notes", "")
            receipt = serializer.validated_data.get("receipt_number") or f"BT-{payment.public_reference}"
            mark_payment_completed(payment, receipt=receipt)
            send_bank_verified_email.delay(str(payment.id))
        else:
            payment.status = "failed"
            payment.failure_reason = serializer.validated_data.get("notes", "Bank transfer rejected")[:250]
            payment.bank_verified_by = request.user
            payment.bank_verified_at = timezone.now()
            payment.save()
        AuditLog.objects.create(
            actor=request.user,
            action="verify" if approve else "reject",
            entity_type="payment",
            entity_id=str(payment.id),
            before=before,
            after={"status": payment.status},
            ip_address=client_ip(request),
        )
        return Response({"success": True, "data": PaymentSerializer(payment).data})

class PendingBankTransfersView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def get(self, request):
        qs = Payment.objects.filter(method="bank", status="pending_verification").order_by("-created_at")
        return Response({"success": True, "data": PaymentSerializer(qs, many=True).data})