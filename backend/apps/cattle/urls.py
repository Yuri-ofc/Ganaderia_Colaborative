from rest_framework.routers import SimpleRouter

from .views import VistaBovinos, VistaMovimientosPotrero, VistaPotreros, VistaRazas

router = SimpleRouter()
router.register("breeds", VistaRazas, basename="breed")
router.register("lots", VistaPotreros, basename="lot")
router.register("cattle", VistaBovinos, basename="cattle")
router.register("lot-movements", VistaMovimientosPotrero, basename="lot-movement")

urlpatterns = router.urls
