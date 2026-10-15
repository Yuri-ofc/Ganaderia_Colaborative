from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from apps.common.serializers import (
    CampoRelacionadoConAlcance,
    exigir_acceso_finca,
    exigir_personal,
    fincas_accesibles,
    fincas_administradas,
    relacion_inmutable,
    usuario_actual,
)
from apps.farms.models import Finca

from .models import Bovino, MovimientoPotrero, Potrero, Raza


def potreros_accesibles(usuario):
    return Potrero.objects.filter(finca__in=fincas_accesibles(usuario), eliminado_en__isnull=True)


def bovinos_accesibles(usuario):
    return Bovino.objects.filter(finca__in=fincas_accesibles(usuario), eliminado_en__isnull=True)


class SerializerRaza(serializers.ModelSerializer):
    class Meta:
        model = Raza
        fields = ("id", "nombre", "creado_en", "actualizado_en")
        read_only_fields = ("id", "creado_en", "actualizado_en")

    def validate(self, atributos):
        exigir_personal(self)
        nombre = atributos.get("nombre", getattr(self.instance, "nombre", None))
        existentes = Raza.objects.filter(nombre=nombre, eliminado_en__isnull=True)
        if self.instance:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise serializers.ValidationError({"nombre": "Esta raza ya existe."})
        return atributos


class SerializerPotrero(serializers.ModelSerializer):
    finca = CampoRelacionadoConAlcance(queryset=Finca.objects.all(), alcance=fincas_administradas)

    class Meta:
        model = Potrero
        fields = ("id", "finca", "nombre", "creado_en", "actualizado_en")
        read_only_fields = ("id", "creado_en", "actualizado_en")

    def validate(self, atributos):
        finca = self.instance.finca if self.instance else atributos["finca"]
        exigir_acceso_finca(self, finca, administrar=True)
        if self.instance:
            relacion_inmutable(atributos, self.instance, "finca")
        nombre = atributos.get("nombre", getattr(self.instance, "nombre", None))
        existentes = Potrero.objects.filter(finca=finca, nombre=nombre, eliminado_en__isnull=True)
        if self.instance:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise serializers.ValidationError({"nombre": "Ya existe un potrero con este nombre en la finca."})
        return atributos


class SerializerBovino(serializers.ModelSerializer):
    finca = CampoRelacionadoConAlcance(queryset=Finca.objects.all(), alcance=fincas_accesibles)
    potrero = CampoRelacionadoConAlcance(queryset=Potrero.objects.all(), alcance=potreros_accesibles)
    raza = serializers.PrimaryKeyRelatedField(queryset=Raza.objects.filter(eliminado_en__isnull=True))

    class Meta:
        model = Bovino
        fields = (
            "id", "finca", "potrero", "arete", "raza", "sexo", "categoria_productiva",
            "estado_fisiologico", "fecha_nacimiento_estimada", "estado_operativo", "url_foto_perfil",
            "perfil_aprobado_por", "creado_por", "desactivado_en", "motivo_desactivacion",
            "creado_en", "actualizado_en",
        )
        read_only_fields = (
            "id", "estado_operativo", "perfil_aprobado_por", "creado_por",
            "desactivado_en", "motivo_desactivacion", "creado_en", "actualizado_en",
        )

    def validate(self, atributos):
        finca = self.instance.finca if self.instance else atributos["finca"]
        exigir_acceso_finca(self, finca)
        if self.instance:
            relacion_inmutable(atributos, self.instance, "finca")
            relacion_inmutable(atributos, self.instance, "potrero")
        potrero = atributos.get("potrero", getattr(self.instance, "potrero", None))
        if potrero.finca_id != finca.pk:
            raise serializers.ValidationError({"potrero": "El potrero debe pertenecer a la misma finca."})
        arete = atributos.get("arete", getattr(self.instance, "arete", None))
        existentes = Bovino.objects.filter(finca=finca, arete=arete, eliminado_en__isnull=True)
        if self.instance:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise serializers.ValidationError({"arete": "Este arete ya existe en la finca."})
        nacimiento = atributos.get(
            "fecha_nacimiento_estimada", getattr(self.instance, "fecha_nacimiento_estimada", None)
        )
        if nacimiento and nacimiento > timezone.localdate():
            raise serializers.ValidationError({"fecha_nacimiento_estimada": "La fecha no puede ser futura."})
        return atributos

    def create(self, datos_validados):
        return super().create({**datos_validados, "creado_por": usuario_actual(self)})


class SerializerMovimientoPotrero(serializers.ModelSerializer):
    bovino = CampoRelacionadoConAlcance(queryset=Bovino.objects.all(), alcance=bovinos_accesibles)
    potrero = CampoRelacionadoConAlcance(queryset=Potrero.objects.all(), alcance=potreros_accesibles)

    class Meta:
        model = MovimientoPotrero
        fields = (
            "id", "bovino", "potrero", "iniciado_en", "finalizado_en", "creado_por",
            "creado_en", "actualizado_en",
        )
        read_only_fields = ("id", "creado_por", "creado_en", "actualizado_en")

    def validate(self, atributos):
        bovino = self.instance.bovino if self.instance else atributos["bovino"]
        exigir_acceso_finca(self, bovino.finca)
        if self.instance:
            for campo in ("bovino", "potrero"):
                relacion_inmutable(atributos, self.instance, campo)
            if "iniciado_en" in atributos and atributos["iniciado_en"] != self.instance.iniciado_en:
                raise serializers.ValidationError({"iniciado_en": "La fecha inicial no se puede cambiar."})
        potrero = atributos.get("potrero", getattr(self.instance, "potrero", None))
        if potrero.finca_id != bovino.finca_id:
            raise serializers.ValidationError({"potrero": "El potrero debe pertenecer a la finca del bovino."})
        iniciado_en = atributos.get("iniciado_en", getattr(self.instance, "iniciado_en", None))
        finalizado_en = atributos.get("finalizado_en", getattr(self.instance, "finalizado_en", None))
        if finalizado_en is not None and finalizado_en < iniciado_en:
            raise serializers.ValidationError({"finalizado_en": "Debe ser posterior al inicio."})
        if finalizado_en is None and iniciado_en > timezone.now():
            raise serializers.ValidationError({"iniciado_en": "Un movimiento abierto no puede iniciar en el futuro."})
        if self.instance and self.instance.finalizado_en is not None and finalizado_en != self.instance.finalizado_en:
            raise serializers.ValidationError({"finalizado_en": "Un movimiento cerrado es inmutable."})
        superpuestos = MovimientoPotrero.objects.filter(bovino=bovino, eliminado_en__isnull=True).filter(
            Q(finalizado_en__isnull=True) | Q(finalizado_en__gt=iniciado_en)
        )
        if finalizado_en is not None:
            superpuestos = superpuestos.filter(iniciado_en__lt=finalizado_en)
        if self.instance:
            superpuestos = superpuestos.exclude(pk=self.instance.pk)
        if superpuestos.exists():
            raise serializers.ValidationError("El periodo se superpone con otro movimiento del bovino.")
        return atributos

    @transaction.atomic
    def create(self, datos_validados):
        movimiento = super().create({**datos_validados, "creado_por": usuario_actual(self)})
        if movimiento.finalizado_en is None:
            Bovino.objects.filter(pk=movimiento.bovino_id).update(
                potrero=movimiento.potrero, actualizado_en=timezone.now()
            )
        return movimiento
