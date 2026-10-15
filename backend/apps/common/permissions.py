from rest_framework.permissions import BasePermission


class PermisoUsuarioActivo(BasePermission):
    message = "Se requiere un usuario autenticado y activo."

    def has_permission(self, solicitud, vista):
        usuario = solicitud.user
        return bool(usuario.is_authenticated and usuario.is_active and usuario.eliminado_en is None)
