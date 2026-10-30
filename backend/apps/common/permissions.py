from rest_framework.permissions import BasePermission


class PermisoUsuarioActivo(BasePermission):
    message = "Se requiere un usuario autenticado y activo."

    def has_permission(self, solicitud, vista):
        usuario = solicitud.user
        activo = bool(usuario.is_authenticated and usuario.is_active and usuario.eliminado_en is None)
        if not activo:
            return False

        # Las vistas que no representan una acción de negocio (login, perfil,
        # logout y raíz de la API) no requieren recurso. Cada vista de negocio
        # declara explícitamente su código de recurso de cuatro caracteres.
        recurso = getattr(vista, "recurso_requerido", None)
        if not recurso:
            return True
        if usuario.is_superuser:
            return True

        # Importación diferida: evita cargar los modelos RBAC antes del registro
        # de aplicaciones durante las migraciones.
        from apps.rbac.models import RolHasRecurso

        return RolHasRecurso.objects.filter(
            rol__asignaciones_usuario__usuario=usuario,
            recurso__nombre=recurso,
        ).exists()
