from django.urls import path

from . import views

urlpatterns = [
    path("", views.SiteContentRootView.as_view(), name="site-content-root"),
    path("bulk/", views.SiteContentBulkView.as_view(), name="site-content-bulk"),
    path("reset/", views.SiteContentResetView.as_view(), name="site-content-reset"),
    path("upload/", views.SiteContentUploadView.as_view(), name="site-content-upload"),
    path("history/", views.RevisionListView.as_view(), name="site-content-history"),
    path("history/<int:pk>/", views.RevisionDetailView.as_view(), name="site-content-history-detail"),
    path("history/<int:pk>/restore/", views.RevisionRestoreView.as_view(), name="site-content-history-restore"),
    path("changesets/", views.ChangeSetListView.as_view(), name="site-content-changesets"),
    path("changesets/<int:pk>/", views.ChangeSetDetailView.as_view(), name="site-content-changeset-detail"),
    path("changesets/<int:pk>/revert/", views.ChangeSetRevertView.as_view(), name="site-content-changeset-revert"),
    path("snapshots/", views.SnapshotListView.as_view(), name="site-content-snapshots"),
    path("snapshots/<int:pk>/", views.SnapshotDetailView.as_view(), name="site-content-snapshot-detail"),
    path("snapshots/<int:pk>/restore/", views.SnapshotRestoreView.as_view(), name="site-content-snapshot-restore"),
    path("key/<str:key>/history/", views.KeyHistoryView.as_view(), name="site-content-key-history"),
    path("<str:key>/", views.SiteContentItemView.as_view(), name="site-content-item"),
]
