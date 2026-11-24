from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import SerializerRegistro

from .models import Recurso, Rol
from .services import recursos_efectivos

Usuario = get_user_model()


class SerializerRecurso(serializers.ModelSerializer):
    class Meta:
        model = Recurso
        fields = ("idrecurso", "nombre", "etiqueta", "opcion_menu")
        read_only_fields = ("opcion_menu",)

    def validate_nombre(self, valor):
        return valor.strip().upper()

    def validate_etiqueta(self, valor):
        # Sin espacios repetidos ni en los extremos; vacío vuelve al código.
        valor = " ".join((valor or "").split())
        if valor:
            repetidas = Recurso.objects.filter(etiqueta__iexact=valor)
            if self.instance is not None:
                repetidas = repetidas.exclude(pk=self.instance.pk)
            if repetidas.exists():
                raise serializers.ValidationError("Ya existe otra opción con esa etiqueta.")
        return valor

    def to_representation(self, instancia):
        datos = super().to_representation(instancia)
        datos["etiqueta"] = instancia.etiqueta_visible
        return datos


class SerializerNuevoUsuario(SerializerRegistro):
    """Alta de cuenta desde Control de acceso: mismas reglas que el registro.

    Se reutiliza ``SerializerRegistro`` para que la contraseña se guarde con
    ``set_password`` y las validaciones de usuario, correo y teléfono sean las
    de siempre; así el inicio de sesión funciona sin ningún cambio. El correo
    es obligatorio porque el login de la aplicación se hace con correo.
    """

    email = serializers.EmailField()


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
    return roles, sorted(recursos_efectivos(usuario))
