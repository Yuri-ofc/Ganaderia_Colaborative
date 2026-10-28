from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from apps.common.serializers import (
    CampoRelacionadoConAlcance,
    exigir_acceso_finca,
    fincas_administradas,
    relacion_inmutable,
    usuario_actual,
)

from .models import Finca, Invitacion, Membresia

Usuario = get_user_model()


class SerializerFinca(serializers.ModelSerializer):
    mi_rol = serializers.SerializerMethodField()

    class Meta:
        model = Finca
        fields = ("id", "propietario", "nombre", "ubicacion", "mi_rol", "creado_en", "actualizado_en")
        read_only_fields = ("id", "propietario", "creado_en", "actualizado_en")

    def get_mi_rol(self, finca):
        usuario = self.context["request"].user
        if finca.propietario_id == usuario.pk:
            return "propietario"
        membresia = Membresia.objects.filter(
            finca=finca, usuario=usuario, eliminado_en__isnull=True
        ).values_list("rol", flat=True).first()
        return membresia

    def validate(self, atributos):
        usuario = usuario_actual(self)
        if self.instance and self.instance.propietario_id != usuario.pk:
            raise PermissionDenied("Solo el propietario puede modificar la finca.")
        return atributos

    def create(self, datos_validados):
        return super().create({**datos_validados, "propietario": usuario_actual(self)})


class SerializerMembresia(serializers.ModelSerializer):
    finca = CampoRelacionadoConAlcance(queryset=Finca.objects.all(), alcance=fincas_administradas)
    usuario = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(eliminado_en__isnull=True)
    )

    class Meta:
        model = Membresia
        fields = ("id", "finca", "usuario", "rol", "invitado_por", "creado_en", "actualizado_en")
        read_only_fields = ("id", "invitado_por", "creado_en", "actualizado_en")

    def validate(self, atributos):
        actor = usuario_actual(self)
        finca = self.instance.finca if self.instance else atributos["finca"]
        exigir_acceso_finca(self, finca, administrar=True)
        if self.instance:
            relacion_inmutable(atributos, self.instance, "finca")
            relacion_inmutable(atributos, self.instance, "usuario")
        miembro = atributos.get("usuario", getattr(self.instance, "usuario", None))
        rol = atributos.get("rol", getattr(self.instance, "rol", None))
        if miembro.pk == finca.propietario_id:
            raise serializers.ValidationError({"usuario": "El propietario ya administra la finca."})
        if (
            rol == Membresia.Rol.ADMINISTRADOR
            or (self.instance and self.instance.rol == Membresia.Rol.ADMINISTRADOR)
        ) and finca.propietario_id != actor.pk:
            raise PermissionDenied("Solo el propietario puede asignar el rol de administrador.")
        existentes = Membresia.objects.filter(finca=finca, usuario=miembro, eliminado_en__isnull=True)
        if self.instance:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise serializers.ValidationError({"usuario": "Este usuario ya es miembro activo de la finca."})
        return atributos

    def create(self, datos_validados):
        return super().create({**datos_validados, "invitado_por": usuario_actual(self)})


class SerializerInvitacion(serializers.ModelSerializer):
    finca = CampoRelacionadoConAlcance(queryset=Finca.objects.all(), alcance=fincas_administradas)
    estado = serializers.ChoiceField(choices=Invitacion.Estado.choices, required=False)

    class Meta:
        model = Invitacion
        fields = (
            "id", "finca", "telefono", "email", "rol", "token", "estado", "expira_en",
            "creado_por", "aceptado_por", "aceptado_en", "creado_en", "actualizado_en",
        )
        read_only_fields = (
            "id", "token", "creado_por", "aceptado_por", "aceptado_en", "creado_en", "actualizado_en",
        )

    def validate(self, atributos):
        actor = usuario_actual(self)
        finca = self.instance.finca if self.instance else atributos["finca"]
        exigir_acceso_finca(self, finca, administrar=True)
        if self.instance:
            relacion_inmutable(atributos, self.instance, "finca")
            if self.instance.estado != Invitacion.Estado.PENDIENTE:
                raise serializers.ValidationError("Solo se pueden modificar invitaciones pendientes.")
            if atributos.get("estado", Invitacion.Estado.PENDIENTE) not in (
                Invitacion.Estado.PENDIENTE, Invitacion.Estado.CANCELADA
            ):
                raise serializers.ValidationError({"estado": "Solo se puede cancelar una invitación pendiente."})
        elif atributos.get("estado", Invitacion.Estado.PENDIENTE) != Invitacion.Estado.PENDIENTE:
            raise serializers.ValidationError({"estado": "Las invitaciones nuevas deben quedar pendientes."})
        rol = atributos.get("rol", getattr(self.instance, "rol", None))
        if rol == Membresia.Rol.ADMINISTRADOR and finca.propietario_id != actor.pk:
            raise PermissionDenied("Solo el propietario puede invitar administradores.")
        expira_en = atributos.get("expira_en", getattr(self.instance, "expira_en", None))
        estado = atributos.get("estado", getattr(self.instance, "estado", Invitacion.Estado.PENDIENTE))
        if estado == Invitacion.Estado.PENDIENTE and expira_en <= timezone.now():
            raise serializers.ValidationError({"expira_en": "La fecha de vencimiento debe ser futura."})
        telefono = atributos.get("telefono", getattr(self.instance, "telefono", None))
        if estado == Invitacion.Estado.PENDIENTE:
            existentes = Invitacion.objects.filter(
                finca=finca, telefono=telefono, estado=Invitacion.Estado.PENDIENTE, eliminado_en__isnull=True
            )
            if self.instance:
                existentes = existentes.exclude(pk=self.instance.pk)
            if existentes.exists():
                raise serializers.ValidationError({"telefono": "Ya hay una invitación pendiente para este teléfono."})
        return atributos

    def create(self, datos_validados):
        return super().create({**datos_validados, "creado_por": usuario_actual(self)})
