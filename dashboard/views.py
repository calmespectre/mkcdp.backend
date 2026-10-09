from rest_framework.response import Response
from rest_framework.views import APIView
from core.permissions import IsStaffOrSuperuser
from .services import stats

class DashboardStatsView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def get(self, request):
        return Response({"success": True, "data": stats()})