from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def api_health(request):
    return JsonResponse({
        "status": "online",
        "service": "MKCDP API",
        "message": "MKCDP backend is running successfully.",
        "documentation": "/api/docs/",
        "schema": "/api/schema/",
    })


urlpatterns = [
    path("", api_health, name="api-health"),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/auth/", include("accounts.urls")),
    path("api/site-content/", include("content.urls")),
    path("api/sitecontent/", include("content.urls")),
    path("api/content/", include("content.urls")),
    path("api/publications/", include("publications.urls")),
    path("api/donations/", include("donations.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/beneficiaries/", include("beneficiaries.urls")),
    path("api/gifts/", include("gifts.urls")),
    path("api/volunteers/", include("volunteers.urls")),
    path("api/partnerships/", include("partnerships.urls")),
    path("api/safeguarding/", include("safeguarding.urls")),
    path("api/dashboard/", include("dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )