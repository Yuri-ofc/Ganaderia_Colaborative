from decimal import Decimal

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from apps.cattle.models import Bovino
from apps.cattle.serializers import bovinos_accesibles
from apps.common.serializers import (
    CampoRelacionadoConAlcance,
    SerializerSoloCreacion,
    exigir_acceso_finca,
    exigir_personal,
    usuario_actual,
)

from .models import Dispositivo, Medicion, MedidaMorfometrica, ModeloIa, Pesaje, TipoMedida


def dispositivos_propios(usuario):
    return Dispositivo.objects.filter(propietario=usuario, eliminado_en__isnull=True)


def mediciones_accesibles(usuario):
    return Medicion.objects.filter(bovino__in=bovinos_accesibles(usuario), eliminado_en__isnull=True)


def pesajes_accesibles(usuario):
    return Pesaje.objects.filter(bovino__in=bovinos_accesibles(usuario), eliminado_en__isnull=True)


class SerializerDispositivo(serializers.ModelSerializer):
    class Meta:
        model = Dispositivo
        fields = (
            "id", "propietario", "modelo", "sistema_operativo", "ultima_conexion_en",
            "creado_en", "actualizado_en",
        )
        read_only_fields = ("id", "propietario", "ultima_conexion_en", "creado_en", "actualizado_en")

    def validate(self, atributos):
        usuario = usuario_actual(self)
        if self.instance and self.instance.propietario_id != usuario.pk:
            raise PermissionDenied("Este dispositivo pertenece a otro usuario.")
        return atributos

    def create(self, datos_validados):
        return super().create({**datos_validados, "propietario": usuario_actual(self)})


class SerializerModeloIa(serializers.ModelSerializer):
    class Meta:
        model = ModeloIa
        fields = ("id", "version", "calibracion", "activo", "creado_en", "actualizado_en")
        read_only_fields = ("id", "creado_en", "actualizado_en")

    def validate(self, atributos):
        exigir_personal(self)
        return atributos


class SerializerTipoMedida(serializers.ModelSerializer):
    class Meta:
        model = TipoMedida
        fields = ("id", "nombre", "unidad", "creado_en", "actualizado_en")
        read_only_fields = ("id", "creado_en", "actualizado_en")

    def validate(self, atributos):
        exigir_personal(self)
        return atributos


class SerializerMedicion(SerializerSoloCreacion):
    bovino = CampoRelacionadoConAlcance(queryset=Bovino.objects.all(), alcance=bovinos_accesibles)
    dispositivo = CampoRelacionadoConAlcance(
        queryset=Dispositivo.objects.all(), alcance=dispositivos_propios
    )
    modelo_ia = serializers.PrimaryKeyRelatedField(
        queryset=ModeloIa.objects.filter(activo=True, eliminado_en__isnull=True)
    )
    corrige = CampoRelacionadoConAlcance(
        queryset=Medicion.objects.all(), alcance=mediciones_accesibles, allow_null=True, required=False
    )

    class Meta:
        model = Medicion
        fields = (
            "id", "bovino", "creado_por", "dispositivo", "modelo_ia", "capturado_en", "modo_captura",
            "peso_estimado_kg", "intervalo_confianza_min_kg", "intervalo_confianza_max_kg",
            "condicion_corporal", "nivel_confianza", "corrige", "creado_en", "actualizado_en",
        )
        read_only_fields = ("id", "creado_por", "creado_en", "actualizado_en")

    def validate(self, atributos):
        bovino = atributos.get("bovino", getattr(self.instance, "bovino", None))
        exigir_acceso_finca(self, bovino.finca)
        estimado = atributos.get("peso_estimado_kg", getattr(self.instance, "peso_estimado_kg", None))
        minimo = atributos.get(
            "intervalo_confianza_min_kg", getattr(self.instance, "intervalo_confianza_min_kg", None)
        )
        maximo = atributos.get(
            "intervalo_confianza_max_kg", getattr(self.instance, "intervalo_confianza_max_kg", None)
        )
        if estimado <= 0 or minimo < 0 or maximo < minimo or not minimo <= estimado <= maximo:
            raise serializers.ValidationError(
                {"peso_estimado_kg": "El peso debe ser positivo y estar dentro del intervalo válido."}
            )
        if atributos.get("condicion_corporal", getattr(self.instance, "condicion_corporal", None)) <= 0:
            raise serializers.ValidationError({"condicion_corporal": "Debe ser positivo."})
        confianza = atributos.get("nivel_confianza", getattr(self.instance, "nivel_confianza", None))
        if not Decimal("0") <= confianza <= Decimal("100"):
            raise serializers.ValidationError({"nivel_confianza": "Debe estar entre 0 y 100."})
        corrige = atributos.get("corrige")
        if corrige and corrige.bovino_id != bovino.pk:
            raise serializers.ValidationError({"corrige": "La corrección debe referirse al mismo bovino."})
        return atributos

    def create(self, datos_validados):
        return super().create({**datos_validados, "creado_por": usuario_actual(self)})


class SerializerMedidaMorfometrica(SerializerSoloCreacion):
    medicion = CampoRelacionadoConAlcance(
        queryset=Medicion.objects.all(), alcance=mediciones_accesibles
    )
    tipo_medida = serializers.PrimaryKeyRelatedField(
        queryset=TipoMedida.objects.filter(eliminado_en__isnull=True)
    )

    class Meta:
        model = MedidaMorfometrica
        fields = ("id", "medicion", "tipo_medida", "valor", "creado_en", "actualizado_en")
        read_only_fields = ("id", "creado_en", "actualizado_en")

    def validate(self, atributos):
        medicion = atributos.get("medicion", getattr(self.instance, "medicion", None))
        exigir_acceso_finca(self, medicion.bovino.finca)
        if atributos.get("valor", getattr(self.instance, "valor", None)) < 0:
            raise serializers.ValidationError({"valor": "No puede ser negativo."})
        tipo_medida = atributos.get("tipo_medida", getattr(self.instance, "tipo_medida", None))
        existentes = MedidaMorfometrica.objects.filter(
            medicion=medicion, tipo_medida=tipo_medida, eliminado_en__isnull=True
        )
        if self.instance:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise serializers.ValidationError({"tipo_medida": "Este tipo ya existe en la medición."})
        return atributos


class SerializerPesaje(SerializerSoloCreacion):
    bovino = CampoRelacionadoConAlcance(queryset=Bovino.objects.all(), alcance=bovinos_accesibles)
    corrige = CampoRelacionadoConAlcance(
        queryset=Pesaje.objects.all(), alcance=pesajes_accesibles, allow_null=True, required=False
    )

    class Meta:
        model = Pesaje
        fields = (
            "id", "bovino", "creado_por", "pesado_en", "tipo_bascula", "peso_real_kg", "corrige",
            "creado_en", "actualizado_en",
        )
        read_only_fields = ("id", "creado_por", "creado_en", "actualizado_en")

    def validate(self, atributos):
        bovino = atributos.get("bovino", getattr(self.instance, "bovino", None))
        exigir_acceso_finca(self, bovino.finca)
        peso = atributos.get("peso_real_kg", getattr(self.instance, "peso_real_kg", None))
        if peso <= 0:
            raise serializers.ValidationError({"peso_real_kg": "El peso debe ser positivo."})
        corrige = atributos.get("corrige")
        if corrige and corrige.bovino_id != bovino.pk:
            raise serializers.ValidationError({"corrige": "La corrección debe referirse al mismo bovino."})
        return atributos

    def create(self, datos_validados):
        return super().create({**datos_validados, "creado_por": usuario_actual(self)})
