from django.urls import path

from .views import (
    SiteContentListView,
    SiteContentBulkUpdateView,
    SiteContentUploadView,
    SiteContentEditDetailView,
    SiteContentResetView,
    SiteContentVersionListView,
)

urlpatterns = [
    path("", SiteContentListView.as_view()),
    path("bulk/", SiteContentBulkUpdateView.as_view()),
    path("upload/", SiteContentUploadView.as_view()),
    path("reset/", SiteContentResetView.as_view()),
    path("versions/", SiteContentVersionListView.as_view()),
    path("edit/<path:key>/", SiteContentEditDetailView.as_view()),
]