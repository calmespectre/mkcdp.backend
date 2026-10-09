from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from .models import GiftNeed, GiftOrder, GiftOrderItem
from .serializers import GiftNeedSerializer, GiftOrderSerializer, GiftOrderCreateSerializer
from core.permissions import IsStaffOrSuperuser
from core.utils import reference
from donations.serializers import CURRENCY_RATES

class GiftNeedViewSet(viewsets.ModelViewSet):
    serializer_class = GiftNeedSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "published", "available"]
    search_fields = ["title", "child_name", "child_location", "category"]
    ordering_fields = ["display_order", "price_kes", "created_at"]

    def get_queryset(self):
        qs = GiftNeed.objects.all()
        if not (self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser)):
            qs = qs.filter(published=True)
        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsStaffOrSuperuser()]

class GiftOrderCreateView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payment"

    def post(self, request):
        serializer = GiftOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        currency = data["currency"].upper()
        rate = CURRENCY_RATES.get(currency)
        if not rate:
            return Response({"success": False, "errors": {"currency": ["Unsupported currency."]}}, status=400)
        if data.get("idempotency_key"):
            existing = GiftOrder.objects.filter(idempotency_key=data["idempotency_key"]).first()
            if existing:
                return Response({"success": True, "data": GiftOrderSerializer(existing).data})
        with transaction.atomic():
            need_ids = [i["id"] for i in data["items"]]
            needs = {n.id: n for n in GiftNeed.objects.select_for_update().filter(id__in=need_ids, published=True, available=True)}
            if len(needs) != len(set(need_ids)):
                return Response({"success": False, "errors": {"items": ["One or more items are unavailable."]}}, status=400)
            order = GiftOrder.objects.create(
                reference=reference("GFT"),
                donor=request.user if request.user.is_authenticated else None,
                name=data["name"].strip(),
                email=data["email"].lower().strip(),
                phone=data.get("phone", "").strip(),
                currency=currency,
                exchange_rate=rate,
                payment_method=data["payment_method"],
                status="awaiting_payment",
                idempotency_key=data.get("idempotency_key", ""),
            )
            total = Decimal("0")
            for item in data["items"]:
                need = needs[item["id"]]
                qty = item["quantity"]
                if need.stock is not None and need.stock < qty:
                    transaction.set_rollback(True)
                    return Response({"success": False, "errors": {"items": [f"Insufficient stock for {need.title}."]}}, status=400)
                line = (need.price_kes * qty).quantize(Decimal("0.01"))
                total += line
                GiftOrderItem.objects.create(
                    order=order, need=need, quantity=qty, unit_price_kes=need.price_kes,
                    title_snapshot=need.title, child_name_snapshot=need.child_name,
                )
                if need.stock is not None:
                    need.stock -= qty
                    if need.stock == 0:
                        need.available = False
                    need.save(update_fields=["stock", "available", "updated_at"])
            order.total_kes = total
            order.total_local = (total / rate).quantize(Decimal("0.01")) if rate else total
            order.save(update_fields=["total_kes", "total_local", "updated_at"])
        from payments.services import initiate_payment
        payment = initiate_payment(gift_order=order, method=data["payment_method"])
        from payments.serializers import PaymentSerializer
        return Response({
            "success": True,
            "data": {
                "order": GiftOrderSerializer(order).data,
                "payment": PaymentSerializer(payment).data,
                "next_action": payment.next_action(),
            },
        }, status=201)

class GiftOrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GiftOrder.objects.all().order_by("-created_at")
    serializer_class = GiftOrderSerializer
    permission_classes = [IsStaffOrSuperuser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "currency", "payment_method"]
    search_fields = ["reference", "email", "name"]