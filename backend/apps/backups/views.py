from rest_framework import mixins, viewsets

from apps.common.serializers import fincas_propias
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
    recurso_requerido = "RESP"
    # RF-24/RNF-17 (recogidos en SESION_RBAC.md): operaciones sensibles del
    # respaldo quedan reservadas al propietario, incluida su consulta.
    roles_permitidos_por_accion = {
        "list": ("PROP",), "retrieve": ("PROP",), "create": ("PROP",),
    }

    def get_queryset(self):
        consulta = Respaldo.objects.filter(
            finca__in=fincas_propias(self.request.user), eliminado_en__isnull=True
        ).select_related("finca", "creado_por")
        finca_id = parametro_uuid(self.request, "finca")
        if finca_id:
            consulta = consulta.filter(finca_id=finca_id)
        return consulta.order_by("-creado_en", "-id")
