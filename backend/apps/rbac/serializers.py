from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Recurso, Rol

Usuario = get_user_model()


class SerializerRecurso(serializers.ModelSerializer):
    class Meta:
        model = Recurso
        fields = ("idrecurso", "nombre")

    def validate_nombre(self, valor):
        return valor.strip().upper()


class SerializerRol(serializers.ModelSerializer):
    recursos = SerializerRecurso(many=True, read_only=True)
    recursos_ids = serializers.PrimaryKeyRelatedField(
        source="recursos", queryset=Recurso.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Rol
        fields = ("Rol_ID", "Rol_nombre", "recursos", "recursos_ids")

    def validate_Rol_nombre(self, valor):
        return valor.strip().upper()

    def create(self, datos_validados):
        recursos = datos_validados.pop("recursos", [])
        rol = Rol.objects.create(**datos_validados)
        rol.recursos.set(recursos)
        return rol

    def update(self, instancia, datos_validados):
        recursos = datos_validados.pop("recursos", None)
        instancia = super().update(instancia, datos_validados)
        if recursos is not None:
            instancia.recursos.set(recursos)
        return instancia


class SerializerUsuarioRbac(serializers.ModelSerializer):
    roles = SerializerRol(source="roles_rbac", many=True, read_only=True)

    class Meta:
        model = Usuario
        fields = ("id", "username", "email", "roles")
        read_only_fields = fields


def roles_y_recursos_usuario(usuario):
    roles = Rol.objects.filter(asignaciones_usuario__usuario=usuario).prefetch_related("recursos").distinct()
    return roles, sorted({recurso.nombre for rol in roles for recurso in rol.recursos.all()})
