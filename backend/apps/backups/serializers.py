from rest_framework import serializers

from apps.common.serializers import (
    CampoRelacionadoConAlcance,
    SerializerSoloCreacion,
    fincas_propias,
    usuario_actual,
)
from apps.farms.models import Finca

from .models import Respaldo


class SerializerRespaldo(SerializerSoloCreacion):
    """El cliente elige la finca y si va cifrado; el resto lo calcula el servidor.

    La ubicación, el tamaño y la suma de verificación salen del archivo que se
    acaba de escribir: si los pudiera enviar el cliente, un respaldo podría
    declarar una integridad que no tiene.
    """

    finca = CampoRelacionadoConAlcance(queryset=Finca.objects.all(), alcance=fincas_propias)
    integridad_verificada = serializers.SerializerMethodField()

    class Meta:
        model = Respaldo
        fields = (
            "id", "finca", "creado_por", "url_almacenamiento", "suma_verificacion", "tamano_bytes",
            "version", "cifrado", "integridad_verificada", "creado_en", "actualizado_en",
        )
        read_only_fields = (
            "id", "creado_por", "url_almacenamiento", "suma_verificacion", "tamano_bytes",
            "version", "creado_en", "actualizado_en",
        )

    def get_integridad_verificada(self, instancia):
        from .services import verificar_integridad

        return verificar_integridad(instancia)

    def validate(self, atributos):
        # RF-24/RNF-17: crear, exportar o restaurar respaldos es del dueño.
        if not fincas_propias(usuario_actual(self)).filter(pk=atributos["finca"].pk).exists():
            raise serializers.ValidationError("Solo el propietario puede gestionar respaldos.")
        return atributos
