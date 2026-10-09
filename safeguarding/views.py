from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import SafeguardingReport, SafeguardingNote
from .serializers import SafeguardingSubmitSerializer, SafeguardingReportSerializer, SafeguardingNoteSerializer
from core.permissions import IsSafeguardingOfficer
from core.utils import reference

class SafeguardingSubmitView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "anon"

    def post(self, request):
        s = SafeguardingSubmitSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        report = SafeguardingReport.objects.create(
            reference=reference("SG"),
            anonymous=data["anonymous"],
            reporter_type=data["reporter_type"],
            full_name="" if data["anonymous"] else data.get("full_name", "").strip(),
            phone="" if data["anonymous"] else data.get("phone", "").strip(),
            email="" if data["anonymous"] else data.get("email", "").lower().strip(),
            relationship=data["relationship"],
            child_name=data.get("child_name", "").strip(),
            location=data["location"].strip(),
            concerns=data["concerns"],
            urgency=data["urgency"],
            description=data["description"].strip(),
            contact_preference=data["contact_preference"],
            acknowledged_at=timezone.now(),
        )
        from notifications.tasks import send_safeguarding_ack
        send_safeguarding_ack.delay(str(report.id))
        from payments.tasks import _broadcast_admin
        _broadcast_admin({"type": "admin.event", "event": "safeguarding_report", "data": {"id": str(report.id), "reference": report.reference, "urgency": report.urgency}})
        return Response({"success": True, "data": {"reference": report.reference}}, status=201)

class SafeguardingReportViewSet(viewsets.ModelViewSet):
    queryset = SafeguardingReport.objects.all().order_by("-created_at")
    serializer_class = SafeguardingReportSerializer
    permission_classes = [IsSafeguardingOfficer]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["status", "urgency", "anonymous"]
    search_fields = ["reference", "child_name", "location"]

class SafeguardingNoteViewSet(viewsets.ModelViewSet):
    queryset = SafeguardingNote.objects.all().order_by("-created_at")
    serializer_class = SafeguardingNoteSerializer
    permission_classes = [IsSafeguardingOfficer]
    filterset_fields = ["report"]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)