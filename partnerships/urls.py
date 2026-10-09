from rest_framework.routers import DefaultRouter
from .views import PartnershipEnquiryViewSet

router = DefaultRouter()
router.register("", PartnershipEnquiryViewSet, basename="partnership")

urlpatterns = router.urls