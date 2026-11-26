from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import VistaExportaciones, VistaRespaldos

router = SimpleRouter()
router.register("backups", VistaRespaldos, basename="backup")

urlpatterns = router.urls + [
    path("exports/", VistaExportaciones.as_view(), name="export-list"),
]
