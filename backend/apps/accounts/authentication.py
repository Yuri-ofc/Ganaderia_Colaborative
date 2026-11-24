"""Autenticación por token con caducidad configurable.

DRF conserva los tokens para siempre. Para una API de campo conviene que una
credencial filtrada deje de servir sola. El plazo se controla con
``API_TOKEN_TTL_DIAS``; ``0`` desactiva la caducidad.
"""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


def token_vencido(token):
    """Indica si el token superó ``API_TOKEN_TTL_DIAS`` desde su creación."""

    dias = getattr(settings, "API_TOKEN_TTL_DIAS", 0)
    return bool(dias and token.created and timezone.now() - token.created > timedelta(days=dias))


class TokenAutenticacion(TokenAuthentication):
    def authenticate_credentials(self, key):
        usuario, token = super().authenticate_credentials(key)
        if token_vencido(token):
            # Se revoca al detectarlo: el cliente recibe 401 y vuelve al login.
            token.delete()
            raise AuthenticationFailed("La sesión expiró. Inicia sesión de nuevo.")
        return usuario, token
