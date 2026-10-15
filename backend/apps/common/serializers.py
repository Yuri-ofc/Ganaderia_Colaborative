from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from apps.farms.models import Finca, Membresia


def usuario_actual(serializer):
    solicitud = serializer.context.get("request")
    if (
        solicitud is None
        or not solicitud.user.is_authenticated
        or not solicitud.user.is_active
        or solicitud.user.eliminado_en is not None
    ):
        raise PermissionDenied("Se requiere un usuario autenticado en el contexto del serializer.")
    return solicitud.user


def fincas_accesibles(usuario):
    if usuario is None or not usuario.is_authenticated or not usuario.is_active or usuario.eliminado_en is not None:
        return Finca.objects.none()
    return Finca.objects.filter(eliminado_en__isnull=True).filter(
        Q(propietario=usuario)
        | Q(membresias__usuario=usuario, membresias__eliminado_en__isnull=True)
    ).distinct()


def fincas_administradas(usuario):
    if usuario is None or not usuario.is_authenticated or not usuario.is_active or usuario.eliminado_en is not None:
        return Finca.objects.none()
    return Finca.objects.filter(eliminado_en__isnull=True).filter(
        Q(propietario=usuario)
        | Q(
            membresias__usuario=usuario,
            membresias__rol=Membresia.Rol.ADMINISTRADOR,
            membresias__eliminado_en__isnull=True,
        )
    ).distinct()


def exigir_acceso_finca(serializer, finca, *, administrar=False):
    usuario = usuario_actual(serializer)
    fincas = fincas_administradas(usuario) if administrar else fincas_accesibles(usuario)
    if not fincas.filter(pk=finca.pk).exists():
        raise PermissionDenied("No tiene permiso sobre esta finca.")
    return usuario


def exigir_personal(serializer):
    usuario = usuario_actual(serializer)
    if not usuario.is_staff:
        raise PermissionDenied("Solo el personal autorizado puede modificar este catálogo.")
    return usuario


def relacion_inmutable(atributos, instancia, campo):
    valor = atributos.get(campo)
    if valor is not None and valor.pk != getattr(instancia, f"{campo}_id"):
        raise serializers.ValidationError({campo: "Esta relación no se puede cambiar."})


class CampoRelacionadoConAlcance(serializers.PrimaryKeyRelatedField):
    def __init__(self, *, alcance, **kwargs):
        self.alcance = alcance
        super().__init__(**kwargs)

    def get_queryset(self):
        solicitud = self.context.get("request")
        if (
            solicitud is None
            or not solicitud.user.is_authenticated
            or not solicitud.user.is_active
            or solicitud.user.eliminado_en is not None
        ):
            return super().get_queryset().none()
        return self.alcance(solicitud.user)


class SerializerSoloCreacion(serializers.ModelSerializer):
    def update(self, instancia, datos_validados):
        raise PermissionDenied("Este registro histórico es inmutable; cree una corrección nueva.")
