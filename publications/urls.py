from django.urls import path

from .views import PublicationListView, PublicationDetailView

urlpatterns = [
    path("", PublicationListView.as_view()),
    path("<int:pk>/", PublicationDetailView.as_view()),
]