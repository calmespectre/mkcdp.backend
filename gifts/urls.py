from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import GiftNeedViewSet, GiftOrderCreateView, GiftOrderViewSet

router = DefaultRouter()
router.register("needs", GiftNeedViewSet, basename="gift-need")
router.register("orders", GiftOrderViewSet, basename="gift-order")

urlpatterns = [
    path("orders/create/", GiftOrderCreateView.as_view()),
] + router.urls