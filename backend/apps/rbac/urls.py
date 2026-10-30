from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import VistaRecursos, VistaRoles, VistaRolesUsuario, VistaUsuariosRbac

router = SimpleRouter()
router.register("roles", VistaRoles, basename="rbac-role")
router.register("resources", VistaRecursos, basename="rbac-resource")

urlpatterns = [
    path("usuarios/", VistaUsuariosRbac.as_view(), name="rbac-users"),
    path("usuarios/<uuid:usuario_id>/roles/", VistaRolesUsuario.as_view(), name="rbac-user-roles"),
] + router.urls
