from rest_framework import serializers

from apps.common.serializers import (
    CampoRelacionadoConAlcance,
    SerializerSoloCreacion,
    exigir_acceso_finca,
    fincas_accesibles,
    usuario_actual,
)
from apps.farms.models import Finca
from apps.measurements.models import Dispositivo
from apps.measurements.serializers import dispositivos_propios

from .models import CambioSincronizacion


class SerializerCambioSincronizacion(SerializerSoloCreacion):
    finca = CampoRelacionadoConAlcance(queryset=Finca.objects.all(), alcance=fincas_accesibles)
    dispositivo = CampoRelacionadoConAlcance(
        queryset=Dispositivo.objects.all(), alcance=dispositivos_propios
    )

    class Meta:
        model = CambioSincronizacion
        fields = (
            "id", "finca", "dispositivo", "creado_por", "id_cambio_cliente", "recurso",
            "id_objeto", "accion", "contenido", "sincronizado_en", "creado_en", "actualizado_en",
        )
        read_only_fields = ("id", "creado_por", "sincronizado_en", "creado_en", "actualizado_en")

    def validate(self, atributos):
        finca = atributos.get("finca", getattr(self.instance, "finca", None))
        exigir_acceso_finca(self, finca)
        dispositivo = atributos.get("dispositivo", getattr(self.instance, "dispositivo", None))
        id_cambio = atributos.get("id_cambio_cliente", getattr(self.instance, "id_cambio_cliente", None))
        existentes = CambioSincronizacion.objects.filter(
            dispositivo=dispositivo, id_cambio_cliente=id_cambio
        )
        if self.instance:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise serializers.ValidationError(
                {"id_cambio_cliente": "Este cambio ya fue recibido desde el dispositivo."}
            )
        return atributos

    def create(self, datos_validados):
        return super().create({**datos_validados, "creado_por": usuario_actual(self)})
