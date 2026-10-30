from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.common.serializers import fincas_accesibles
from apps.common.views import parametro_uuid

from .models import CambioSincronizacion
from .serializers import SerializerCambioSincronizacion


class VistaCambiosSincronizacion(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SerializerCambioSincronizacion
    recurso_requerido = "SYNC"

    def get_queryset(self):
        consulta = CambioSincronizacion.objects.filter(
            finca__in=fincas_accesibles(self.request.user), eliminado_en__isnull=True
        ).select_related("finca", "dispositivo", "creado_por")
        finca_id = parametro_uuid(self.request, "finca")
        dispositivo_id = parametro_uuid(self.request, "dispositivo")
        if finca_id:
            consulta = consulta.filter(finca_id=finca_id)
        if dispositivo_id:
            consulta = consulta.filter(dispositivo_id=dispositivo_id)
        return consulta.order_by("-creado_en", "-id")

    @action(detail=True, methods=("post",), url_path="acknowledge", url_name="acknowledge")
    def confirmar(self, request, pk=None):
        cambio = self.get_object()
        if cambio.dispositivo.propietario_id != request.user.pk:
            raise PermissionDenied("Solo el propietario del dispositivo puede confirmar este cambio.")
        if cambio.sincronizado_en is None:
            cambio.sincronizado_en = timezone.now()
            cambio.save(update_fields=("sincronizado_en", "actualizado_en"))
        return Response(self.get_serializer(cambio).data)
