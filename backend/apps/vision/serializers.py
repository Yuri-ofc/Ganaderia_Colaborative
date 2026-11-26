from django.conf import settings
from rest_framework import serializers

from apps.cattle.models import Bovino
from apps.cattle.serializers import bovinos_accesibles
from apps.common.serializers import (
    CampoRelacionadoConAlcance,
    SerializerSoloCreacion,
    exigir_acceso_finca,
)
from apps.measurements.serializers import SerializerMedicion

from .models import CapturaVision


def capturas_accesibles(usuario):
    return CapturaVision.objects.filter(
        bovino__in=bovinos_accesibles(usuario), eliminado_en__isnull=True
    )


class SerializerCapturaVision(SerializerSoloCreacion):
    bovino = CampoRelacionadoConAlcance(queryset=Bovino.objects.all(), alcance=bovinos_accesibles)
    medicion_detalle = SerializerMedicion(source="medicion", read_only=True)

    class Meta:
        model = CapturaVision
        fields = (
            "id", "bovino", "creado_por", "archivo", "tipo_archivo", "medicion",
            "medicion_detalle", "creado_en", "actualizado_en",
        )
        read_only_fields = ("id", "creado_por", "medicion", "creado_en", "actualizado_en")

    def validate(self, atributos):
        exigir_acceso_finca(self, atributos["bovino"].finca)
        archivo = atributos["archivo"]
        limite = settings.VISION_TAMANO_MAXIMO_MB * 1024 * 1024
        if archivo.size > limite:
            raise serializers.ValidationError(
                {"archivo": f"El archivo supera el máximo de {settings.VISION_TAMANO_MAXIMO_MB} MB."}
            )
        return atributos
