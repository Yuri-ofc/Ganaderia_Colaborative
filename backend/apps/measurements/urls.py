from rest_framework.routers import SimpleRouter

from .views import (
    VistaDispositivos,
    VistaMediciones,
    VistaMedidasMorfometricas,
    VistaModelosIa,
    VistaPesajes,
    VistaTiposMedida,
)

router = SimpleRouter()
router.register("devices", VistaDispositivos, basename="device")
router.register("ai-models", VistaModelosIa, basename="ai-model")
router.register("measurement-types", VistaTiposMedida, basename="measurement-type")
router.register("measurements", VistaMediciones, basename="measurement")
router.register("morphometric-measurements", VistaMedidasMorfometricas, basename="morphometric-measurement")
router.register("scale-weighings", VistaPesajes, basename="scale-weighing")

urlpatterns = router.urls
