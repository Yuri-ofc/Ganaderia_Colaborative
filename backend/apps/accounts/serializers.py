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
        from apps.rbac.services import roles_efectivos

        # Roles efectivos, no solo las asignaciones explícitas: un propietario
        # sin rol RBAC asignado también actúa como PROP. El campo ``recursos``
        # se calcula con la misma fuente, así que ambos quedan coherentes.
        return sorted(roles_efectivos(usuario))

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

    def validate_email(self, valor):
        correo = (valor or "").strip()
        if not correo:
            return ""
        if Usuario.objects.filter(email__iexact=correo, eliminado_en__isnull=True).exists():
            raise serializers.ValidationError("Este correo ya está registrado.")
        return correo

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

        # ``email`` no identifica una cuenta de forma unívoca en bases antiguas:
        # se prueba cada candidato hasta encontrar el que valida la contraseña.
        # Así una fila duplicada nunca produce un error 500.
        if email:
            candidatos = Usuario.objects.filter(email__iexact=email).order_by("date_joined", "pk")
        else:
            candidatos = Usuario.objects.filter(username=username)

        usuario = None
        for candidato in candidatos:
            autenticado = authenticate(
                request=self.context.get("request"),
                username=candidato.username,
                password=password,
            )
            if autenticado:
                usuario = autenticado
                break

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
