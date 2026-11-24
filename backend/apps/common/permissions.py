from rest_framework.permissions import BasePermission

from apps.rbac.services import puede_ejecutar, recurso_requerido


class PermisoUsuarioActivo(BasePermission):
    message = "Se requiere un usuario autenticado y activo."

    def has_permission(self, solicitud, vista):
        usuario = solicitud.user
        activo = bool(usuario.is_authenticated and usuario.is_active and usuario.eliminado_en is None)
        if not activo:
            return False

        # Login, perfil y logout no declaran recurso. Toda ruta de negocio sí;
        # las excepciones por acción se resuelven aquí, nunca en el cliente.
        return puede_ejecutar(usuario, recurso_requerido(vista), vista=vista)
