from rest_framework.routers import SimpleRouter

from .views import VistaCapturasVision

router = SimpleRouter()
router.register("vision-captures", VistaCapturasVision, basename="vision-capture")

urlpatterns = router.urls
