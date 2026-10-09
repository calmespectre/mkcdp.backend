from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from .models import Opportunity, VolunteerApplication
from .serializers import OpportunitySerializer, VolunteerApplicationSerializer, VolunteerApplicationCreateSerializer
from core.permissions import IsStaffOrSuperuser

class OpportunityViewSet(viewsets.ModelViewSet):
    serializer_class = OpportunitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["published", "archived"]
    search_fields = ["title", "org", "location", "description"]

    def get_queryset(self):
        qs = Opportunity.objects.all()
        if not (self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser)):
            qs = qs.filter(published=True, archived=False)
        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsStaffOrSuperuser()]

    def perform_create(self, serializer):
        if not serializer.validated_data.get("code"):
            from core.utils import reference
            serializer.validated_data["code"] = reference("VOL")
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)

class VolunteerApplicationCreateView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "anon"

    def post(self, request):
        s = VolunteerApplicationCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        try:
            opp = Opportunity.objects.get(id=data["opportunity_id"], published=True, archived=False)
        except Opportunity.DoesNotExist:
            return Response({"success": False, "errors": {"opportunity_id": ["Opportunity not found."]}}, status=404)
        app_obj = VolunteerApplication.objects.create(
            opportunity=opp,
            full_name=data["full_name"].strip(),
            phone=data["phone"].strip(),
            email=data.get("email", "").lower().strip(),
            availability=data["availability"],
            note=data.get("note", ""),
        )
        from notifications.tasks import send_volunteer_confirmation
        send_volunteer_confirmation.delay(str(app_obj.id))
        from payments.tasks import _broadcast_admin
        _broadcast_admin({"type": "admin.event", "event": "volunteer_application", "data": {"id": str(app_obj.id), "opportunity": opp.title}})
        return Response({"success": True, "data": VolunteerApplicationSerializer(app_obj).data}, status=201)

class VolunteerApplicationViewSet(viewsets.ModelViewSet):
    queryset = VolunteerApplication.objects.all().order_by("-created_at")
    serializer_class = VolunteerApplicationSerializer
    permission_classes = [IsStaffOrSuperuser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "opportunity"]
    search_fields = ["full_name", "phone", "email"]