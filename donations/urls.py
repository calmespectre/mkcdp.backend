from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import DonationCreateView, DonationViewSet, MyDonationsView

router = DefaultRouter()
router.register("", DonationViewSet, basename="donation")

urlpatterns = [
    path("create/", DonationCreateView.as_view(), name="donation-create"),
    path("mine/", MyDonationsView.as_view(), name="donation-mine"),
] + router.urls