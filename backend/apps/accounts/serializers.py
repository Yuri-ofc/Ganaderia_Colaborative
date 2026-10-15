from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

Usuario = get_user_model()


class SerializerRegistro(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = ("id", "username", "email", "telefono", "password")
        read_only_fields = ("id",)

    def validate_password(self, valor):
        validate_password(valor, user=Usuario(username=self.initial_data.get("username", "")))
        return valor

    def validate_telefono(self, valor):
        if not valor:
            return None
        if Usuario.objects.filter(telefono=valor, eliminado_en__isnull=True).exists():
            raise serializers.ValidationError("Este teléfono ya está registrado.")
        return valor

    def create(self, datos_validados):
        clave = datos_validados.pop("password")
        usuario = Usuario(**datos_validados)
        usuario.set_password(clave)
        usuario.save()
        return usuario


class SerializerInicioSesion(AuthTokenSerializer):
    def validate(self, atributos):
        atributos = super().validate(atributos)
        if atributos["user"].eliminado_en is not None:
            raise serializers.ValidationError(
                {"detail": "Esta cuenta fue eliminada."}, code="authorization"
            )
        return atributos
