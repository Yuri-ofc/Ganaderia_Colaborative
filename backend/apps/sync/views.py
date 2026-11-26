from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.common.serializers import fincas_accesibles
from apps.common.views import parametro_uuid

from .models import CambioSincronizacion
from .serializers import SerializerCambioSincronizacion, SerializerGrupoConflicto
from .services import grupos_en_conflicto, resolver_conflicto


class VistaCambiosSincronizacion(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SerializerCambioSincronizacion
    recurso_requerido = "SYNC"
    roles_permitidos_por_accion = {
        "list": ("PROP", "ADMI", "OPER"), "retrieve": ("PROP", "ADMI", "OPER"),
        "create": ("PROP", "ADMI", "OPER"), "confirmar": ("PROP", "ADMI", "OPER"),
        "conflictos": ("PROP", "ADMI", "OPER"),
        # Elegir qué cambio sobrevive afecta a los datos de toda la finca, no
        # solo al dispositivo que lo subió.
        "resolver": ("PROP", "ADMI"),
    }

    def get_queryset(self):
        consulta = CambioSincronizacion.objects.filter(
            finca__in=fincas_accesibles(self.request.user), eliminado_en__isnull=True
        ).select_related("finca", "dispositivo", "creado_por")
        finca_id = parametro_uuid(self.request, "finca")
        dispositivo_id = parametro_uuid(self.request, "dispositivo")
        estado = self.request.query_params.get("estado")
        recurso = self.request.query_params.get("recurso")
        if finca_id:
            consulta = consulta.filter(finca_id=finca_id)
        if dispositivo_id:
            consulta = consulta.filter(dispositivo_id=dispositivo_id)
        if estado in CambioSincronizacion.Estado.values:
            consulta = consulta.filter(estado=estado)
        if recurso:
            consulta = consulta.filter(recurso=recurso)
        return consulta.order_by("-creado_en", "-id")

    def _finca_del_parametro(self):
        finca_id = parametro_uuid(self.request, "finca")
        if not finca_id:
            raise ValidationError({"finca": "Indique la finca de la cola a revisar."})
        finca = fincas_accesibles(self.request.user).filter(pk=finca_id).first()
        if finca is None:
            raise NotFound("Finca no encontrada.")
        return finca

    @action(detail=True, methods=("post",), url_path="acknowledge", url_name="acknowledge")
    def confirmar(self, request, pk=None):
        cambio = self.get_object()
        if cambio.dispositivo.propietario_id != request.user.pk:
            raise PermissionDenied("Solo el propietario del dispositivo puede confirmar este cambio.")
        if cambio.estado == CambioSincronizacion.Estado.DESCARTADO:
            raise ValidationError(
                {"estado": "Este cambio se descartó al resolver un conflicto; no se sincroniza."}
            )
        if cambio.sincronizado_en is None:
            cambio.sincronizado_en = timezone.now()
            cambio.estado = CambioSincronizacion.Estado.SINCRONIZADO
            cambio.save(update_fields=("sincronizado_en", "estado", "actualizado_en"))
        return Response(self.get_serializer(cambio).data)

    @action(detail=False, methods=("get",), url_path="conflicts", url_name="conflicts")
    def conflictos(self, request):
        grupos = grupos_en_conflicto(self._finca_del_parametro())
        return Response(SerializerGrupoConflicto(grupos, many=True).data)

    @action(detail=True, methods=("post",), url_path="resolve", url_name="resolve")
    def resolver(self, request, pk=None):
        ganador = self.get_object()
        if ganador.estado != CambioSincronizacion.Estado.CONFLICTO:
            raise ValidationError({"estado": "Este cambio no está en conflicto."})
        resuelto = resolver_conflicto(ganador, request.user)
        return Response(self.get_serializer(resuelto).data)
