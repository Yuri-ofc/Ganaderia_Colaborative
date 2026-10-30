from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

Usuario = get_user_model()


class SerializerPerfilUsuario(serializers.ModelSerializer):
    """Representación mínima del usuario que inició sesión."""

    roles = serializers.SerializerMethodField()
    recursos = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ("id", "username", "email", "telefono", "is_superuser", "roles", "recursos")
        read_only_fields = fields

    def get_roles(self, usuario):
        from apps.rbac.serializers import roles_y_recursos_usuario

        roles, _ = roles_y_recursos_usuario(usuario)
        return [rol.Rol_nombre for rol in roles]

    def get_recursos(self, usuario):
        from apps.rbac.serializers import roles_y_recursos_usuario

        _, recursos = roles_y_recursos_usuario(usuario)
        return recursos


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


class SerializerInicioSesion(serializers.Serializer):
    """Acepta ``email`` o ``username`` junto con ``password``.

    El frontend usa correo electrónico; se conserva el nombre de usuario
    para compatibilidad con clientes existentes de la API.
    """

    email = serializers.EmailField(label="Correo electrónico", required=False)
    username = serializers.CharField(label="Usuario", required=False)
    password = serializers.CharField(
        label="Contraseña",
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    def validate(self, atributos):
        email = atributos.get("email")
        username = atributos.get("username")
        password = atributos.get("password")

        if not email and not username:
            raise serializers.ValidationError({"detail": "Indique correo electrónico o usuario."})
        if email and username:
            raise serializers.ValidationError({"detail": "Use correo electrónico o usuario, no ambos."})
        try:
            usuario_obj = Usuario.objects.get(email__iexact=email) if email else Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Credenciales inválidas."}, code="authorization"
            )

        # Autenticar con username + password
        usuario = authenticate(
            request=self.context.get("request"),
            username=usuario_obj.username,
            password=password,
        )

        if not usuario:
            raise serializers.ValidationError(
                {"detail": "Credenciales inválidas."}, code="authorization"
            )

        if usuario.eliminado_en is not None:
            raise serializers.ValidationError(
                {"detail": "Esta cuenta fue eliminada."}, code="authorization"
            )

        atributos["user"] = usuario
        return atributos
