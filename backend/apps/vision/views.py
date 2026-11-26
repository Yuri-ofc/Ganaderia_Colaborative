from django.db import transaction
from rest_framework import mixins, viewsets
from rest_framework.parsers import FormParser, MultiPartParser

from apps.common.serializers import usuario_actual
from apps.common.views import parametro_uuid

from .models import CapturaVision
from .serializers import SerializerCapturaVision, capturas_accesibles
from .services import crear_medicion_simulada


class VistaCapturasVision(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SerializerCapturaVision
    recurso_requerido = "VCOM"
    roles_permitidos_por_accion = {
        "list": ("PROP", "ADMI", "OPER"), "retrieve": ("PROP", "ADMI", "OPER"),
        "create": ("PROP", "ADMI", "OPER"),
    }
    # El contrato por defecto del API es JSON; la captura llega como archivo.
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        consulta = capturas_accesibles(self.request.user).select_related(
            "bovino", "creado_por", "medicion"
        )
        finca_id = parametro_uuid(self.request, "finca")
        bovino_id = parametro_uuid(self.request, "bovino")
        if finca_id:
            consulta = consulta.filter(bovino__finca_id=finca_id)
        if bovino_id:
            consulta = consulta.filter(bovino_id=bovino_id)
        return consulta.order_by("-creado_en", "-id")

    def perform_create(self, serializer):
        usuario = usuario_actual(serializer)
        bovino = serializer.validated_data["bovino"]
        # La captura y su medición se guardan juntas: una captura sin medición
        # no tendría nada que mostrar, y una medición sin captura perdería su
        # origen.
        with transaction.atomic():
            medicion = crear_medicion_simulada(
                bovino, usuario, serializer.validated_data["tipo_archivo"]
            )
            serializer.save(creado_por=usuario, medicion=medicion)
