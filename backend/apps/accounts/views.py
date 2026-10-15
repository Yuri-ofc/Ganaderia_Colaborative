from rest_framework import generics, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.common.permissions import PermisoUsuarioActivo

from .serializers import SerializerInicioSesion, SerializerRegistro


class VistaRegistro(generics.CreateAPIView):
    serializer_class = SerializerRegistro
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "registration"


class VistaInicioSesion(ObtainAuthToken):
    serializer_class = SerializerInicioSesion
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"


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
