import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.serializers.json import DjangoJSONEncoder

class PaymentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.reference = self.scope["url_route"]["kwargs"]["reference"]
        self.group_name = f"payment_{self.reference}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        payload = await self._current_status()
        if payload:
            await self.send(text_data=json.dumps(payload, cls=DjangoJSONEncoder))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def payment_status(self, event):
        await self.send(text_data=json.dumps(event["payload"], cls=DjangoJSONEncoder))

    @database_sync_to_async
    def _current_status(self):
        from .models import Payment
        p = Payment.objects.filter(public_reference=self.reference).first()
        if not p:
            return None
        return {
            "type": "payment.status",
            "reference": p.public_reference,
            "status": p.status,
            "method": p.method,
            "amount": str(p.amount),
            "currency": p.currency,
            "receipt_number": p.receipt_number,
        }

class AdminEventsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated or not (user.is_staff or user.is_superuser):
            await self.close(code=4403)
            return
        self.group_name = "admin_events"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def admin_event(self, event):
        await self.send(text_data=json.dumps(event["payload"], cls=DjangoJSONEncoder))