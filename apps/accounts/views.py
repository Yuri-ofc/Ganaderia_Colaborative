from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.common.views import ActiveUserPermission

from .serializers import RegistrationSerializer


class RegistrationView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "registration"


class LoginView(ObtainAuthToken):
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"


class LogoutView(APIView):
    permission_classes = (ActiveUserPermission,)

    def post(self, request):
        request.auth.delete()
        return Response({"detail": "Sesión cerrada."})
