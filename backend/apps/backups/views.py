from rest_framework import mixins, viewsets

from apps.common.serializers import fincas_administradas
from apps.common.views import parametro_uuid

from .models import Respaldo
from .serializers import SerializerRespaldo


class VistaRespaldos(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SerializerRespaldo

    def get_queryset(self):
        consulta = Respaldo.objects.filter(
            finca__in=fincas_administradas(self.request.user), eliminado_en__isnull=True
        ).select_related("finca", "creado_por")
        finca_id = parametro_uuid(self.request, "finca")
        if finca_id:
            consulta = consulta.filter(finca_id=finca_id)
        return consulta.order_by("-creado_en", "-id")
