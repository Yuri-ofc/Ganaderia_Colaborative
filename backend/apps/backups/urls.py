from rest_framework.routers import SimpleRouter

from .views import VistaRespaldos

router = SimpleRouter()
router.register("backups", VistaRespaldos, basename="backup")

urlpatterns = router.urls
