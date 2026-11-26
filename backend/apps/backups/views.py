from django.conf import settings
from django.http import HttpResponse
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.serializers import fincas_propias
from apps.common.views import parametro_uuid

from .models import Respaldo
from .serializers import SerializerRespaldo
from .services import (
    CONJUNTOS_EXPORTABLES,
    bytes_para_descarga,
    exportar_finca,
    generar_respaldo,
    restaurar_respaldo,
)


def _descarga(nombre, tipo_contenido, contenido):
    respuesta = HttpResponse(contenido, content_type=tipo_contenido)
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
    respuesta["Content-Length"] = str(len(contenido))
    return respuesta


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
        "descargar": ("PROP",), "restaurar": ("PROP",),
    }
    # Restaurar es un permiso aparte de ver o generar: se puede confiar a
    # alguien el respaldo sin darle la facultad de sobrescribir la finca.
    recursos_por_accion = {"restaurar": "RECU"}

    def get_queryset(self):
        consulta = Respaldo.objects.filter(
            finca__in=fincas_propias(self.request.user), eliminado_en__isnull=True
        ).select_related("finca", "creado_por")
        finca_id = parametro_uuid(self.request, "finca")
        if finca_id:
            consulta = consulta.filter(finca_id=finca_id)
        return consulta.order_by("-creado_en", "-id")

    def perform_create(self, serializer):
        """Genera el archivo de verdad; el POST no registra metadatos sueltos.

        Sin ``cifrado`` explícito se usa el cifrado solo si el servidor tiene
        clave configurada, y la respuesta dice en qué quedó. Pedirlo cifrado sin
        clave es un error, nunca un respaldo en claro silencioso.
        """
        cifrado = serializer.validated_data.get(
            "cifrado", bool(settings.RESPALDO_CLAVE_CIFRADO)
        )
        serializer.instance = generar_respaldo(
            serializer.validated_data["finca"],
            self.request.user,
            cifrado=cifrado,
            base_url=self.request.build_absolute_uri("/"),
        )

    @action(detail=True, methods=("get",), url_path="download", url_name="download")
    def descargar(self, request, pk=None):
        respaldo = self.get_object()
        contenido = bytes_para_descarga(respaldo)
        sufijo = "json.enc" if respaldo.cifrado else "json"
        return _descarga(
            f"respaldo-{respaldo.pk}.{sufijo}", "application/octet-stream", contenido
        )

    @action(detail=True, methods=("post",), url_path="restore", url_name="restore")
    def restaurar(self, request, pk=None):
        respaldo = self.get_object()
        if request.data.get("confirmar") is not True:
            raise ValidationError(
                {
                    "confirmar": "Restaurar reemplaza los datos actuales de la finca. "
                    "Envíe confirmar=true para continuar."
                }
            )
        restaurado = restaurar_respaldo(respaldo, request.user)
        return Response(
            {"respaldo": str(respaldo.pk), "restaurado": restaurado}, status=status.HTTP_200_OK
        )


class VistaExportaciones(APIView):
    """Datos de la finca en CSV o JSON para usarlos fuera del sistema.

    No es un respaldo: no va cifrado, no se guarda en el servidor y no sirve
    para restaurar.
    """

    recurso_requerido = "EXPO"

    def get(self, solicitud):
        finca_id = parametro_uuid(solicitud, "finca")
        if not finca_id:
            raise ValidationError({"finca": "Indique la finca a exportar."})
        finca = fincas_propias(solicitud.user).filter(pk=finca_id).first()
        if finca is None:
            raise NotFound("Finca no encontrada.")
        incluir = [
            nombre.strip()
            for nombre in solicitud.query_params.get("incluir", "").split(",")
            if nombre.strip()
        ]
        nombre, tipo_contenido, contenido = exportar_finca(
            finca,
            formato=solicitud.query_params.get("formato", "csv"),
            incluir=incluir or list(CONJUNTOS_EXPORTABLES),
        )
        return _descarga(nombre, tipo_contenido, contenido)
