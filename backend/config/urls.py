from django.contrib import admin
from django.urls import include, path

from apps.common.views import VistaRaizApi
from apps.common.module_views import VistaModuloPendiente

api_v1_patterns = [
    path("", VistaRaizApi.as_view(), name="api-root"),
    path("auth/", include("apps.accounts.urls")),
    path("rbac/", include("apps.rbac.urls")),
    path(
        "modules/vision/",
        VistaModuloPendiente.as_view(
            recurso_requerido="VCOM", modulo="vision-computacional", nombre="Visión computacional",
            punto_extension="apps.vision: análisis de captura y perfil de bovino",
        ),
        name="module-vision",
    ),
    path(
        "modules/exports/",
        VistaModuloPendiente.as_view(
            recurso_requerido="EXPO", modulo="exportaciones", nombre="Exportaciones",
            punto_extension="apps.backups: exportación de datos de finca",
        ),
        name="module-exports",
    ),
    path(
        "modules/recovery/",
        VistaModuloPendiente.as_view(
            recurso_requerido="RECU", modulo="recuperacion", nombre="Recuperación",
            punto_extension="apps.backups: recuperación verificada de respaldos",
        ),
        name="module-recovery",
    ),
    path("", include("apps.farms.urls")),
    path("", include("apps.cattle.urls")),
    path("", include("apps.measurements.urls")),
    path("", include("apps.backups.urls")),
    path("", include("apps.sync.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
]
