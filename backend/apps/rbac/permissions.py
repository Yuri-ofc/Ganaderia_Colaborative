from apps.common.permissions import PermisoUsuarioActivo


class TieneRecurso(PermisoUsuarioActivo):
    """Alias de compatibilidad; la política vive en PermisoUsuarioActivo."""

    message = "No tiene el permiso requerido para esta acción."
