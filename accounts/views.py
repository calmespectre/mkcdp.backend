from django.db import transaction
from rest_framework import status, viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, VerificationCode
from .serializers import (
    UserSerializer,
    AdminUserSerializer,
    AdminUserCreateSerializer,
    SignupSerializer,
    SigninSerializer,
    VerifySerializer,
    ResendSerializer,
)
from core.models import AuditLog
from core.permissions import IsStaffOrSuperuser
from core.utils import client_ip


def tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def auth_payload(user, extra=None):
    payload = {"user": UserSerializer(user).data}
    if extra:
        payload.update(extra)
    return payload


class SignupView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "anon"

    @transaction.atomic
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        code = VerificationCode.issue(user, "signup")
        from notifications.tasks import send_verification_code_email
        send_verification_code_email.delay(str(user.id), code.code, "signup")
        AuditLog.objects.create(
            actor=user,
            action="create",
            entity_type="user",
            entity_id=str(user.id),
            after={"email": user.email},
            ip_address=client_ip(request),
            request_id=getattr(request, "request_id", ""),
        )
        return Response(
            {
                "success": True,
                "data": auth_payload(user, {"requires_verification": True}),
            },
            status=201,
        )


class SigninView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "anon"

    def post(self, request):
        serializer = SigninSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        AuditLog.objects.create(
            actor=user,
            action="login",
            entity_type="user",
            entity_id=str(user.id),
            ip_address=client_ip(request),
        )
        if not user.is_email_verified:
            code = VerificationCode.issue(user, "signin")
            from notifications.tasks import send_verification_code_email
            send_verification_code_email.delay(str(user.id), code.code, "signin")
            return Response(
                {
                    "success": True,
                    "data": auth_payload(user, {"requires_verification": True}),
                }
            )
        return Response(
            {
                "success": True,
                "data": auth_payload(
                    user,
                    {
                        "tokens": tokens_for(user),
                        "requires_verification": False,
                    },
                ),
            }
        )


class VerifyView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "anon"

    def post(self, request):
        serializer = VerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        code_value = serializer.validated_data["code"]
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response(
                {"success": False, "errors": {"detail": ["Account not found."]}},
                status=404,
            )
        code = (
            VerificationCode.objects.filter(user=user, code=code_value, used=False)
            .order_by("-created_at")
            .first()
        )
        if not code or not code.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": {"code": ["Invalid or expired code."]},
                },
                status=400,
            )
        with transaction.atomic():
            code.used = True
            code.save(update_fields=["used", "updated_at"])
            if not user.is_email_verified:
                user.is_email_verified = True
                user.save(update_fields=["is_email_verified", "updated_at"])
        AuditLog.objects.create(
            actor=user,
            action="login",
            entity_type="user",
            entity_id=str(user.id),
            after={"verified": True},
            ip_address=client_ip(request),
        )
        return Response(
            {
                "success": True,
                "data": auth_payload(user, {"tokens": tokens_for(user)}),
            }
        )


class ResendView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "anon"

    def post(self, request):
        serializer = ResendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        purpose = serializer.validated_data["purpose"]
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({"success": True, "message": "If that email exists, a code was sent."})
        if user.is_email_verified:
            return Response({"success": True, "message": "Already verified."})
        code = VerificationCode.issue(user, purpose)
        from notifications.tasks import send_verification_code_email
        send_verification_code_email.delay(str(user.id), code.code, purpose)
        return Response({"success": True, "message": "Code sent."})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except Exception:
                pass
        return Response({"success": True, "message": "Logged out."})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"success": True, "data": UserSerializer(request.user).data})

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})

    def delete(self, request):
        request.user.is_active = False
        request.user.is_email_verified = False
        request.user.save(update_fields=["is_active", "is_email_verified", "updated_at"])
        return Response({"success": True, "message": "Account deactivated."})


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    permission_classes = [IsStaffOrSuperuser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_staff", "is_superuser", "is_email_verified"]
    search_fields = ["email", "username", "first_name", "last_name", "phone", "country"]
    ordering_fields = ["created_at", "email"]

    def get_serializer_class(self):
        if self.action == "create":
            return AdminUserCreateSerializer
        return AdminUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"success": True, "data": AdminUserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.id == request.user.id:
            return Response(
                {"success": False, "errors": {"detail": ["You cannot delete your own account."]}},
                status=400,
            )
        instance.delete()
        return Response({"success": True, "message": "User deleted."})