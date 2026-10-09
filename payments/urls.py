from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PaymentStatusView, PaymentViewSet, BankVerifyView, PendingBankTransfersView
from .webhooks import mpesa_webhook, card_webhook

router = DefaultRouter()
router.register("", PaymentViewSet, basename="payment")

urlpatterns = [
    path("status/<str:reference>/", PaymentStatusView.as_view()),
    path("bank/pending/", PendingBankTransfersView.as_view()),
    path("bank/<str:reference>/verify/", BankVerifyView.as_view()),
    path("webhooks/mpesa/", mpesa_webhook),
    path("webhooks/card/", card_webhook),
] + router.urls