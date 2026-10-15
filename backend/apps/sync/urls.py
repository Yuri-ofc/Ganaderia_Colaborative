from rest_framework.routers import SimpleRouter

from .views import VistaCambiosSincronizacion

router = SimpleRouter()
router.register("sync-changes", VistaCambiosSincronizacion, basename="sync-change")

urlpatterns = router.urls
