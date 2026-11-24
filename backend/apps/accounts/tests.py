from django.test import override_settings
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.authtoken.models import Token

from apps.common.testing import CLAVE, PruebaApi, Usuario


class PruebasRegistro(PruebaApi):
    url = reverse_lazy("register")

    def test_el_registro_crea_el_usuario_y_responde_json(self):
        respuesta = self.client.post(
            self.url,
            {
                "username": "nueva_operaria",
                "email": "nueva@example.com",
                "telefono": "+573001112233",
                "password": "Clave.Segura.2026",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta["Content-Type"], "application/json")
        self.assertNotIn("password", respuesta.json())
        usuario = Usuario.objects.get(username="nueva_operaria")
        self.assertTrue(usuario.check_password("Clave.Segura.2026"))
        self.assertIsNone(usuario.eliminado_en)

    def test_el_registro_rechaza_claves_debiles(self):
        respuesta = self.client.post(
            self.url, {"username": "debil", "password": "123"}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", respuesta.json())

    def test_el_registro_rechaza_telefonos_repetidos(self):
        self.crear_usuario("primera", telefono="+573004445566")
        respuesta = self.client.post(
            self.url,
            {"username": "segunda", "telefono": "+573004445566", "password": "Clave.Segura.2026"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("telefono", respuesta.json())

    def test_el_registro_rechaza_correos_repetidos_sin_distinguir_mayusculas(self):
        self.crear_usuario("primera", email="duplicado@example.com")
        respuesta = self.client.post(
            self.url,
            {
                "username": "segunda",
                "email": "Duplicado@Example.com",
                "password": "Clave.Segura.2026",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", respuesta.json())
        self.assertEqual(Usuario.objects.count(), 1)


class PruebasAutenticacionPorToken(PruebaApi):
    def setUp(self):
        super().setUp()
        self.usuario = self.crear_usuario("operaria")

    def test_el_token_abre_la_api(self):
        respuesta = self.client.post(
            reverse("token"), {"username": "operaria", "password": CLAVE}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        llave = respuesta.json()["token"]
        self.assertTrue(Token.objects.filter(key=llave, user=self.usuario).exists())

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {llave}")
        fincas = self.client.get(reverse("farm-list"))
        self.assertEqual(fincas.status_code, status.HTTP_200_OK)
        self.assertEqual(fincas["Content-Type"], "application/json")

    def test_el_correo_compartido_con_una_cuenta_eliminada_no_bloquea_el_acceso(self):
        """Regresión: ``email`` no es un identificador único en bases antiguas.

        Antes de la restricción, ``Usuario.objects.get(email=...)`` lanzaba
        ``MultipleObjectsReturned`` y el login respondía 500.
        """

        self.usuario.email = "compartido@example.com"
        self.usuario.save(update_fields=("email",))

        antigua = self.crear_usuario("antigua", clave="Otra.Clave.2026")
        antigua.email = "compartido@example.com"
        antigua.eliminado_en = timezone.now()
        antigua.save(update_fields=("email", "eliminado_en"))

        respuesta = self.client.post(
            reverse("token"), {"email": "Compartido@Example.com", "password": CLAVE}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.json()["token"], Token.objects.get(user=self.usuario).key)

    def test_la_clave_de_una_cuenta_eliminada_no_abre_sesion_entre_homologos(self):
        self.usuario.email = "compartido@example.com"
        self.usuario.save(update_fields=("email",))

        antigua = self.crear_usuario("antigua", clave="Otra.Clave.2026")
        antigua.email = "compartido@example.com"
        antigua.eliminado_en = timezone.now()
        antigua.save(update_fields=("email", "eliminado_en"))

        respuesta = self.client.post(
            reverse("token"),
            {"email": "compartido@example.com", "password": "Otra.Clave.2026"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", respuesta.json())
        self.assertFalse(Token.objects.filter(user=antigua).exists())
    def test_rechaza_la_clave_incorrecta(self):
        respuesta = self.client.post(
            reverse("token"), {"username": "operaria", "password": "incorrecta"}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rechaza_cuentas_eliminadas(self):
        self.usuario.eliminado_en = timezone.now()
        self.usuario.save(update_fields=("eliminado_en",))
        respuesta = self.client.post(
            reverse("token"), {"username": "operaria", "password": CLAVE}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Token.objects.filter(user=self.usuario).exists())

    def test_el_cierre_de_sesion_revoca_el_token(self):
        self.autenticar(self.usuario)
        respuesta = self.client.post(reverse("logout"))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertFalse(Token.objects.filter(user=self.usuario).exists())
        self.assertEqual(
            self.client.get(reverse("farm-list")).status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_la_api_exige_autenticacion(self):
        self.assertEqual(
            self.client.get(reverse("farm-list")).status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_un_usuario_eliminado_no_puede_usar_su_token(self):
        self.autenticar(self.usuario)
        self.usuario.eliminado_en = timezone.now()
        self.usuario.save(update_fields=("eliminado_en",))
        self.assertEqual(
            self.client.get(reverse("farm-list")).status_code, status.HTTP_403_FORBIDDEN
        )

    @override_settings(API_TOKEN_TTL_DIAS=1)
    def test_un_token_caducado_se_revoca_y_responde_401(self):
        token = self.autenticar(self.usuario)
        Token.objects.filter(pk=token.pk).update(created=timezone.now() - timedelta(days=2))

        respuesta = self.client.get(reverse("farm-list"))

        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Token.objects.filter(pk=token.pk).exists())
