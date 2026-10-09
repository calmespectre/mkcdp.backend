from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SiteContentViewSet,
    ContentRevisionViewSet,
    bulk_content,
    bulk_update_content,
)

router = DefaultRouter()
router.register("revisions", ContentRevisionViewSet, basename="content-revisions")
router.register("", SiteContentViewSet, basename="content")

urlpatterns = [
    path("bulk/", bulk_content, name="content-bulk"),
    path("bulk-update/", bulk_update_content, name="content-bulk-update"),
    path("", include(router.urls)),
]