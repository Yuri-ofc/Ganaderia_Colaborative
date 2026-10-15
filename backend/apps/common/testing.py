from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.farms.models import Finca, Membresia

Usuario = get_user_model()

SIN_LIMITES = {
    **settings.REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {"auth": None, "registration": None},
}

CLAVE = "Clave.Prueba.2026"


@override_settings(
    REST_FRAMEWORK=SIN_LIMITES,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class PruebaApi(APITestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def crear_usuario(self, nombre, *, clave=CLAVE, **extra):
        return Usuario.objects.create_user(username=nombre, password=clave, **extra)

    def crear_finca(self, propietario, nombre=None, **extra):
        return Finca.objects.create(
            propietario=propietario, nombre=nombre or f"Finca de {propietario.username}", **extra
        )

    def agregar_miembro(self, finca, usuario, rol, invitado_por=None):
        return Membresia.objects.create(
            finca=finca, usuario=usuario, rol=rol, invitado_por=invitado_por or finca.propietario
        )

    def autenticar(self, usuario):
        token, _ = Token.objects.get_or_create(user=usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return token

    def desautenticar(self):
        self.client.credentials()
