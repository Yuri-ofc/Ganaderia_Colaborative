from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.common.views import VistaRaizApi

api_v1_patterns = [
    path("", VistaRaizApi.as_view(), name="api-root"),
    path("auth/", include("apps.accounts.urls")),
    path("rbac/", include("apps.rbac.urls")),
    path("", include("apps.farms.urls")),
    path("", include("apps.cattle.urls")),
    path("", include("apps.measurements.urls")),
    path("", include("apps.vision.urls")),
    path("", include("apps.backups.urls")),
    path("", include("apps.sync.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
]

if settings.DEBUG:
    # En desarrollo Django sirve las capturas subidas; en producción las
    # entrega el servidor web desde MEDIA_ROOT.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
