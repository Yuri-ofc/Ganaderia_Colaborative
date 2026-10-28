from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

Usuario = get_user_model()


class SerializerPerfilUsuario(serializers.ModelSerializer):
    """Representación mínima del usuario que inició sesión."""

    class Meta:
        model = Usuario
        fields = ("id", "username", "email", "telefono")
        read_only_fields = fields


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
    """Acepta ``email`` + ``password`` y devuelve el usuario autenticado.

    El frontend envía el campo *email* en lugar de *username*, por lo que
    se busca primero el usuario por email para obtener su username y
    después se autentica con las credenciales estándar de Django.
    """

    email = serializers.EmailField(label="Correo electrónico")
    password = serializers.CharField(
        label="Contraseña",
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    def validate(self, atributos):
        email = atributos.get("email")
        password = atributos.get("password")

        # Buscar el username asociado al email
        try:
            usuario_obj = Usuario.objects.get(email=email)
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
