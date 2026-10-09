from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import SafeguardingSubmitView, SafeguardingReportViewSet, SafeguardingNoteViewSet

router = DefaultRouter()
router.register("reports", SafeguardingReportViewSet, basename="safeguarding-report")
router.register("notes", SafeguardingNoteViewSet, basename="safeguarding-note")

urlpatterns = [
    path("submit/", SafeguardingSubmitView.as_view()),
] + router.urls