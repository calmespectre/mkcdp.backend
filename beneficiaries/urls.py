from rest_framework.routers import DefaultRouter
from .views import BeneficiaryViewSet, SponsorshipViewSet

router = DefaultRouter()
router.register("", BeneficiaryViewSet, basename="beneficiary")
router.register("sponsorships", SponsorshipViewSet, basename="sponsorship")

urlpatterns = router.urls