from rest_framework import serializers

from apps.common.serializers import (
    CampoRelacionadoConAlcance,
    SerializerSoloCreacion,
    exigir_acceso_finca,
    fincas_propias,
    usuario_actual,
)
from apps.farms.models import Finca

from .models import Respaldo


class SerializerRespaldo(SerializerSoloCreacion):
    finca = CampoRelacionadoConAlcance(queryset=Finca.objects.all(), alcance=fincas_propias)

    class Meta:
        model = Respaldo
        fields = (
            "id", "finca", "creado_por", "url_almacenamiento", "suma_verificacion", "tamano_bytes",
            "version", "cifrado", "creado_en", "actualizado_en",
        )
        read_only_fields = ("id", "creado_por", "creado_en", "actualizado_en")

    def validate(self, atributos):
        finca = self.instance.finca if self.instance else atributos["finca"]
        # RF-24/RNF-17: crear, exportar o restaurar respaldos es del dueño.
        if not fincas_propias(usuario_actual(self)).filter(pk=finca.pk).exists():
            raise serializers.ValidationError("Solo el propietario puede gestionar respaldos.")
        if atributos.get("tamano_bytes", getattr(self.instance, "tamano_bytes", None)) <= 0:
            raise serializers.ValidationError({"tamano_bytes": "El archivo debe tener un tamaño positivo."})
        return atributos

    def create(self, datos_validados):
        return super().create({**datos_validados, "creado_por": usuario_actual(self)})
