from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.common.permissions import PermisoUsuarioActivo

from .serializers import SerializerInicioSesion, SerializerPerfilUsuario, SerializerRegistro


class VistaRegistro(generics.CreateAPIView):
    serializer_class = SerializerRegistro
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "registration"


class VistaInicioSesion(ObtainAuthToken):
    serializer_class = SerializerInicioSesion
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        usuario = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=usuario)
        return Response(
            {"token": token.key, "usuario": SerializerPerfilUsuario(usuario).data},
            status=status.HTTP_200_OK,
        )


class VistaCierreSesion(APIView):
    permission_classes = (PermisoUsuarioActivo,)

    def post(self, solicitud):
        if solicitud.auth is None:
            return Response(
                {"detail": "No hay un token de autenticación que cerrar."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        solicitud.auth.delete()
        return Response({"detail": "Sesión cerrada."})


class VistaPerfilUsuario(APIView):
    """Expone únicamente el perfil del usuario autenticado actual."""

    permission_classes = (PermisoUsuarioActivo,)

    def get(self, solicitud):
        return Response(SerializerPerfilUsuario(solicitud.user).data)


class VistaBuscarUsuario(APIView):
    """Busca un usuario activo por nombre de usuario o teléfono.

    Parámetro GET: ``q`` (mínimo 3 caracteres).
    Devuelve hasta 10 coincidencias: id, username, telefono.
    No expone email ni datos sensibles.
    El usuario buscado no puede ser el mismo que hace la búsqueda.
    """

    permission_classes = (PermisoUsuarioActivo,)
    recurso_requerido = "RBAC"

    def get(self, solicitud):
        Usuario = get_user_model()
        q = solicitud.query_params.get("q", "").strip()
        if len(q) < 3:
            return Response([])
        resultados = (
            Usuario.objects
            .filter(eliminado_en__isnull=True, is_active=True)
            .filter(Q(username__icontains=q) | Q(telefono__icontains=q))
            .exclude(pk=solicitud.user.pk)
            .values("id", "username", "telefono")[:10]
        )
        return Response(list(resultados))
