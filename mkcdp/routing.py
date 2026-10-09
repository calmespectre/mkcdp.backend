from django.urls import re_path
from payments.consumers import PaymentConsumer, AdminEventsConsumer

websocket_urlpatterns = [
    re_path(r"^ws/payments/(?P<reference>[\w\-]+)/$", PaymentConsumer.as_asgi()),
    re_path(r"^ws/admin/events/$", AdminEventsConsumer.as_asgi()),
]