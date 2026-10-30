from rest_framework.permissions import BasePermission

from .models import RolHasRecurso


class TieneRecurso(BasePermission):
    """Autoriza en servidor si alguno de los roles del usuario posee el recurso."""

    message = "No tiene el permiso requerido para esta acción."

    def has_permission(self, solicitud, vista):
        usuario = solicitud.user
        if not (usuario.is_authenticated and usuario.is_active and usuario.eliminado_en is None):
            return False
        if usuario.is_superuser:
            return True
        recurso = getattr(vista, "recurso_requerido", None)
        if not recurso:
            return True
        return RolHasRecurso.objects.filter(
            rol__asignaciones_usuario__usuario=usuario,
            recurso__nombre=recurso,
        ).exists()
