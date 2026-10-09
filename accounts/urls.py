from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    SignupView,
    SigninView,
    VerifyView,
    ResendView,
    LogoutView,
    MeView,
    RefreshView,
    AdminUserViewSet,
)

router = DefaultRouter()
router.register("users", AdminUserViewSet, basename="admin-user")

urlpatterns = [
    path("signup/", SignupView.as_view()),
    path("signin/", SigninView.as_view()),
    path("verify/", VerifyView.as_view()),
    path("resend/", ResendView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("me/", MeView.as_view()),
    path("refresh/", RefreshView.as_view()),
] + router.urls