from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import OpportunityViewSet, VolunteerApplicationCreateView, VolunteerApplicationViewSet

router = DefaultRouter()
router.register("opportunities", OpportunityViewSet, basename="opportunity")
router.register("applications", VolunteerApplicationViewSet, basename="volunteer-application")

urlpatterns = [
    path("applications/submit/", VolunteerApplicationCreateView.as_view()),
] + router.urls