from django.urls import reverse, reverse_lazy
from django.utils import timezone
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
