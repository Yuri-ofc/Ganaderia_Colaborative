import shutil
import tempfile
from pathlib import Path

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
        # Respaldos y capturas escriben archivos de verdad. Se redirigen a una
        # carpeta temporal para que ninguna prueba deje basura en el repositorio
        # (una prueba concreta puede volver a redirigirlos si necesita leerlos).
        temporal = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temporal, ignore_errors=True)
        archivos = override_settings(
            RESPALDOS_DIR=Path(temporal) / "respaldos",
            MEDIA_ROOT=Path(temporal) / "media",
        )
        archivos.enable()
        self.addCleanup(archivos.disable)

    def crear_usuario(self, nombre, *, clave=CLAVE, con_permisos_rbac=True, **extra):
        usuario = Usuario.objects.create_user(username=nombre, password=clave, **extra)
        # Las pruebas heredadas se ocupan del aislamiento de finca y no de
        # RBAC. Se les da un rol de fixture con todos los recursos para que
        # continúen verificando esa capa. Las pruebas RBAC lo desactivan.
        if con_permisos_rbac:
            from apps.rbac.constantes import RECURSOS
            from apps.rbac.models import Recurso, Rol, UsuarioHasRol

            recursos = [Recurso.objects.get_or_create(nombre=codigo)[0] for codigo in RECURSOS]
            rol, _ = Rol.objects.get_or_create(Rol_nombre="TEST")
            rol.recursos.set(recursos)
            UsuarioHasRol.objects.get_or_create(usuario=usuario, rol=rol)
        return usuario

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
