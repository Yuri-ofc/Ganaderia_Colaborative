from rest_framework import filters, mixins, viewsets

from apps.common.serializers import fincas_accesibles
from apps.common.views import MixinBorradoLogico, MixinEscrituraPersonal, parametro_uuid

from .models import Dispositivo, Medicion, MedidaMorfometrica, ModeloIa, Pesaje, TipoMedida
from .serializers import (
    SerializerDispositivo,
    SerializerMedicion,
    SerializerMedidaMorfometrica,
    SerializerModeloIa,
    SerializerPesaje,
    SerializerTipoMedida,
)


class VistaDispositivos(MixinBorradoLogico, viewsets.ModelViewSet):
    serializer_class = SerializerDispositivo
    recurso_requerido = "DISP"

    def get_queryset(self):
        return Dispositivo.objects.filter(
            propietario=self.request.user, eliminado_en__isnull=True
        ).order_by("-ultima_conexion_en", "-creado_en", "-id")


class VistaModelosIa(MixinEscrituraPersonal, MixinBorradoLogico, viewsets.ModelViewSet):
    serializer_class = SerializerModeloIa
    recurso_requerido = "MODI"

    def get_queryset(self):
        return ModeloIa.objects.filter(eliminado_en__isnull=True).order_by("-creado_en", "-id")


class VistaTiposMedida(MixinEscrituraPersonal, MixinBorradoLogico, viewsets.ModelViewSet):
    serializer_class = SerializerTipoMedida
    recurso_requerido = "TIPO"

    def get_queryset(self):
        return TipoMedida.objects.filter(eliminado_en__isnull=True).order_by("nombre", "id")


class VistaMediciones(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SerializerMedicion
    recurso_requerido = "MEDI"
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("bovino__arete",)
    ordering_fields = ("capturado_en", "creado_en")
    ordering = ("-capturado_en", "-id")

    def get_queryset(self):
        consulta = Medicion.objects.filter(
            bovino__finca__in=fincas_accesibles(self.request.user), eliminado_en__isnull=True
        ).select_related("bovino", "dispositivo", "modelo_ia", "creado_por")
        finca_id = parametro_uuid(self.request, "finca")
        bovino_id = parametro_uuid(self.request, "bovino")
        if finca_id:
            consulta = consulta.filter(bovino__finca_id=finca_id)
        if bovino_id:
            consulta = consulta.filter(bovino_id=bovino_id)
        return consulta


class VistaMedidasMorfometricas(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SerializerMedidaMorfometrica
    recurso_requerido = "MEDI"

    def get_queryset(self):
        consulta = MedidaMorfometrica.objects.filter(
            medicion__bovino__finca__in=fincas_accesibles(self.request.user),
            medicion__eliminado_en__isnull=True,
            eliminado_en__isnull=True,
        ).select_related("medicion", "tipo_medida")
        medicion_id = parametro_uuid(self.request, "medicion")
        if medicion_id:
            consulta = consulta.filter(medicion_id=medicion_id)
        return consulta.order_by("tipo_medida__nombre", "id")


class VistaPesajes(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SerializerPesaje
    recurso_requerido = "PESA"
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("bovino__arete",)
    ordering_fields = ("pesado_en", "creado_en")
    ordering = ("-pesado_en", "-id")

    def get_queryset(self):
        consulta = Pesaje.objects.filter(
            bovino__finca__in=fincas_accesibles(self.request.user), eliminado_en__isnull=True
        ).select_related("bovino", "creado_por")
        finca_id = parametro_uuid(self.request, "finca")
        bovino_id = parametro_uuid(self.request, "bovino")
        if finca_id:
            consulta = consulta.filter(bovino__finca_id=finca_id)
        if bovino_id:
            consulta = consulta.filter(bovino_id=bovino_id)
        return consulta
