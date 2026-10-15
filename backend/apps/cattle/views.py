from django.utils import timezone
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.common.serializers import exigir_acceso_finca, fincas_accesibles
from apps.common.views import MixinBorradoLogico, MixinEscrituraPersonal, parametro_uuid

from .models import Bovino, MovimientoPotrero, Potrero, Raza
from .serializers import (
    SerializerBovino,
    SerializerMovimientoPotrero,
    SerializerPotrero,
    SerializerRaza,
)


class VistaRazas(MixinEscrituraPersonal, MixinBorradoLogico, viewsets.ModelViewSet):
    serializer_class = SerializerRaza
    filter_backends = (filters.SearchFilter,)
    search_fields = ("nombre",)

    def get_queryset(self):
        return Raza.objects.filter(eliminado_en__isnull=True).order_by("nombre", "id")

    def perform_destroy(self, instancia):
        if instancia.bovinos.filter(eliminado_en__isnull=True).exists():
            raise ValidationError("La raza está asociada a bovinos activos.")
        super().perform_destroy(instancia)


class VistaPotreros(MixinBorradoLogico, viewsets.ModelViewSet):
    serializer_class = SerializerPotrero

    def get_queryset(self):
        consulta = Potrero.objects.filter(
            finca__in=fincas_accesibles(self.request.user), eliminado_en__isnull=True
        ).select_related("finca")
        finca_id = parametro_uuid(self.request, "finca")
        if finca_id:
            consulta = consulta.filter(finca_id=finca_id)
        return consulta.order_by("nombre", "id")

    def perform_destroy(self, instancia):
        exigir_acceso_finca(self.get_serializer(), instancia.finca, administrar=True)
        if instancia.bovinos.filter(eliminado_en__isnull=True).exists():
            raise ValidationError("El potrero contiene bovinos activos.")
        super().perform_destroy(instancia)


class VistaBovinos(MixinBorradoLogico, viewsets.ModelViewSet):
    serializer_class = SerializerBovino
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("arete", "raza__nombre", "potrero__nombre")
    ordering_fields = ("arete", "creado_en", "fecha_nacimiento_estimada")
    ordering = ("arete", "id")

    def get_queryset(self):
        consulta = Bovino.objects.filter(
            finca__in=fincas_accesibles(self.request.user), eliminado_en__isnull=True
        ).select_related("finca", "potrero", "raza", "creado_por")
        finca_id = parametro_uuid(self.request, "finca")
        potrero_id = parametro_uuid(self.request, "potrero")
        if finca_id:
            consulta = consulta.filter(finca_id=finca_id)
        if potrero_id:
            consulta = consulta.filter(potrero_id=potrero_id)
        estado = self.request.query_params.get("estado")
        if estado:
            if estado not in Bovino.EstadoOperativo.values:
                raise ValidationError({"estado": "Estado operativo inválido."})
            consulta = consulta.filter(estado_operativo=estado)
        return consulta

    def perform_destroy(self, instancia):
        exigir_acceso_finca(self.get_serializer(), instancia.finca, administrar=True)
        super().perform_destroy(instancia)

    @action(detail=True, methods=("post",), url_path="approve-profile", url_name="approve-profile")
    def aprobar_perfil(self, request, pk=None):
        bovino = self.get_object()
        exigir_acceso_finca(self.get_serializer(), bovino.finca, administrar=True)
        if bovino.estado_operativo != Bovino.EstadoOperativo.PERFIL_PENDIENTE:
            raise ValidationError("Solo se pueden aprobar perfiles pendientes.")
        bovino.estado_operativo = Bovino.EstadoOperativo.ACTIVO
        bovino.perfil_aprobado_por = request.user
        bovino.save(update_fields=("estado_operativo", "perfil_aprobado_por", "actualizado_en"))
        return Response(self.get_serializer(bovino).data)

    @action(detail=True, methods=("post",), url_path="deactivate", url_name="deactivate")
    def desactivar(self, request, pk=None):
        bovino = self.get_object()
        exigir_acceso_finca(self.get_serializer(), bovino.finca, administrar=True)
        nuevo_estado = request.data.get("estado")
        motivo = request.data.get("motivo", "")
        permitidos = {
            Bovino.EstadoOperativo.VENDIDO,
            Bovino.EstadoOperativo.MUERTO,
            Bovino.EstadoOperativo.RETIRADO,
        }
        if nuevo_estado not in permitidos:
            raise ValidationError({"estado": "Use vendido, muerto o retirado."})
        if not isinstance(motivo, str) or not motivo.strip():
            raise ValidationError({"motivo": "Debe indicar el motivo de baja."})
        motivo = motivo.strip()
        if len(motivo) > 255:
            raise ValidationError({"motivo": "El motivo no puede superar 255 caracteres."})
        if bovino.desactivado_en is not None:
            raise ValidationError("El bovino ya fue dado de baja.")
        bovino.estado_operativo = nuevo_estado
        bovino.desactivado_en = timezone.now()
        bovino.motivo_desactivacion = motivo
        bovino.save(
            update_fields=("estado_operativo", "desactivado_en", "motivo_desactivacion", "actualizado_en")
        )
        return Response(self.get_serializer(bovino).data, status=status.HTTP_200_OK)


class VistaMovimientosPotrero(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SerializerMovimientoPotrero
    http_method_names = ("get", "post", "patch", "head", "options")

    def get_queryset(self):
        consulta = MovimientoPotrero.objects.filter(
            bovino__finca__in=fincas_accesibles(self.request.user),
            bovino__eliminado_en__isnull=True,
            eliminado_en__isnull=True,
        ).select_related("bovino", "potrero", "creado_por")
        bovino_id = parametro_uuid(self.request, "bovino")
        if bovino_id:
            consulta = consulta.filter(bovino_id=bovino_id)
        return consulta.order_by("-iniciado_en", "-id")
