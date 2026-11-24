"""Único punto de cálculo para autorización RBAC.

Los roles del modelo RBAC son globales, mientras que los roles operativos del
dominio viven en una membresía de finca. Este servicio compone ambas fuentes:
el permiso abre el módulo y las consultas/serializadores conservan el alcance
de la finca. Ningún cliente decide permisos.
"""

from apps.farms.models import Membresia

from .models import Rol, RolHasRecurso


CODIGO_SUPERADMIN = "SUPR"
ROLES_OPERATIVOS = frozenset(("PROP", "ADMI", "OPER"))
ROL_POR_MEMBRESIA = {
    Membresia.Rol.ADMINISTRADOR: "ADMI",
    Membresia.Rol.OPERARIO: "OPER",
}


def _usuario_valido(usuario):
    return bool(usuario and usuario.is_authenticated and usuario.is_active and usuario.eliminado_en is None)


def roles_directos(usuario):
    """Códigos asignados explícitamente en ``usuario_has_rol``."""
    if not _usuario_valido(usuario):
        return set()
    # Django reutiliza la instancia autenticada durante toda la solicitud. El
    # permiso, el filtro de finca y el serializer la consultan en cadena; este
    # caché efímero evita repetir el mismo SELECT sin conservar permisos entre
    # peticiones ni retrasar cambios de rol.
    cacheado = getattr(usuario, "_rbac_roles_directos", None)
    if cacheado is not None:
        return set(cacheado)
    roles = set(
        Rol.objects.filter(asignaciones_usuario__usuario=usuario)
        .values_list("Rol_nombre", flat=True)
        .distinct()
    )
    usuario._rbac_roles_directos = frozenset(roles)
    return roles


def es_superadministrador(usuario, *, roles=None):
    if not _usuario_valido(usuario):
        return False
    return bool(usuario.is_superuser or CODIGO_SUPERADMIN in (roles if roles is not None else roles_directos(usuario)))


def roles_efectivos(usuario):
    """Combina roles explícitos con el contexto de las fincas del usuario."""
    if not _usuario_valido(usuario):
        return set()
    cacheado = getattr(usuario, "_rbac_roles_efectivos", None)
    if cacheado is not None:
        return set(cacheado)
    directos = roles_directos(usuario)
    if es_superadministrador(usuario, roles=directos):
        efectivos = directos | ({CODIGO_SUPERADMIN} if usuario.is_superuser else set())
        usuario._rbac_roles_efectivos = frozenset(efectivos)
        return efectivos

    # El propietario se infiere de la finca; las membresías conservan el
    # significado que ya tenía el dominio, sin duplicar ni migrar datos.
    from apps.farms.models import Finca

    if Finca.objects.filter(propietario=usuario, eliminado_en__isnull=True).exists():
        directos.add("PROP")
    directos.update(
        ROL_POR_MEMBRESIA[rol]
        for rol in Membresia.objects.filter(usuario=usuario, eliminado_en__isnull=True)
        .values_list("rol", flat=True)
        if rol in ROL_POR_MEMBRESIA
    )
    usuario._rbac_roles_efectivos = frozenset(directos)
    return directos


def recursos_efectivos(usuario, *, roles=None):
    """Recursos efectivos, consultados sin serializar modelos completos."""
    if not _usuario_valido(usuario):
        return set()
    cacheado = getattr(usuario, "_rbac_recursos_efectivos", None)
    if cacheado is not None:
        return set(cacheado)
    roles = roles if roles is not None else roles_efectivos(usuario)
    if not roles:
        return set()
    recursos = set(
        RolHasRecurso.objects.filter(rol__Rol_nombre__in=roles)
        .values_list("recurso__nombre", flat=True)
        .distinct()
    )
    usuario._rbac_recursos_efectivos = frozenset(recursos)
    return recursos


def recurso_requerido(vista):
    """Resuelve excepciones por acción en una única capa."""
    por_accion = getattr(vista, "recursos_por_accion", {})
    return por_accion.get(getattr(vista, "action", None), getattr(vista, "recurso_requerido", None))


def roles_permitidos_para_accion(vista):
    """Devuelve la política fina de una acción, si la vista la declara.

    ``recurso_requerido`` abre un módulo y este mapa restringe operaciones
    concretas dentro de él.  El alcance de una finca se sigue comprobando en
    las consultas y serializers del dominio: un rol global jamás sustituye
    esa comprobación contextual.
    """
    por_accion = getattr(vista, "roles_permitidos_por_accion", {})
    return por_accion.get(getattr(vista, "action", None))


def puede_iniciar_primera_finca(usuario, vista):
    """Excepción mínima de onboarding: lista vacía y creación inicial."""
    if not getattr(vista, "permite_arranque_sin_recurso", False):
        return False
    if getattr(vista, "action", None) not in {"list", "create"}:
        return False
    from django.db.models import Q
    from apps.farms.models import Finca

    return not Finca.objects.filter(eliminado_en__isnull=True).filter(
        Q(propietario=usuario) | Q(membresias__usuario=usuario, membresias__eliminado_en__isnull=True)
    ).exists()


def puede_ejecutar(usuario, recurso, *, vista=None):
    """Punto único de autorización RBAC para todas las vistas de negocio."""
    if not _usuario_valido(usuario):
        return False
    roles = roles_efectivos(usuario)
    if es_superadministrador(usuario, roles=roles):
        return True

    permitidos = roles_permitidos_para_accion(vista) if vista is not None else None
    # El catálogo permite roles personalizados. Solo los tres roles de finca
    # reciben la restricción fija de la documentación; un rol adicional es una
    # concesión explícita administrada con sus recursos, no una vía implícita
    # para elevar a OPER. Los tests heredados usan el rol artificial TEST para
    # probar alcance de objeto y no representa una cuenta de producción.
    roles_de_finca = roles.intersection(ROLES_OPERATIVOS)
    if permitidos is not None and roles_de_finca and not roles_de_finca.intersection(permitidos):
        return False

    if not recurso:
        return True
    return recurso in recursos_efectivos(usuario, roles=roles) or (
        vista is not None and puede_iniciar_primera_finca(usuario, vista)
    )


# Alias público temporal para las importaciones existentes fuera de este
# módulo. Las decisiones nuevas deben usar ``puede_ejecutar``.
def tiene_recurso(usuario, recurso, *, vista=None):
    return puede_ejecutar(usuario, recurso, vista=vista)
