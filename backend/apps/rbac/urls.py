from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import VistaEtiquetasRecursos, VistaOpcionesMenu, VistaRecursos, VistaRoles, VistaRolesUsuario, VistaUsuariosRbac

router = SimpleRouter()
router.register("roles", VistaRoles, basename="rbac-role")
router.register("resources", VistaRecursos, basename="rbac-resource")

urlpatterns = [
    path("opciones/", VistaOpcionesMenu.as_view(), name="rbac-menu-options"),
    path("etiquetas/", VistaEtiquetasRecursos.as_view(), name="rbac-labels"),
    path("usuarios/", VistaUsuariosRbac.as_view(), name="rbac-users"),
    path("usuarios/<uuid:usuario_id>/roles/", VistaRolesUsuario.as_view(), name="rbac-user-roles"),
] + router.urls
