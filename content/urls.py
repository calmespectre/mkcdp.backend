from django.urls import path
from . import views

urlpatterns = [
    path("bulk/", views.site_content_bulk, name="site-content-bulk"),
    path("reset/", views.site_content_reset, name="site-content-reset"),
    path("upload/", views.site_content_upload, name="site-content-upload"),
    path("<str:key>/", views.site_content_item, name="site-content-item"),
    path("", views.site_content_root, name="site-content-root"),
]