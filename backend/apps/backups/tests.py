from django.urls import reverse
from rest_framework import status

from apps.common.testing import PruebaApi
from apps.farms.models import Membresia

from .models import Respaldo


class PruebasAccesoRespaldos(PruebaApi):
    def setUp(self):
        super().setUp()
        self.propietaria = self.crear_usuario("propietaria")
        self.administradora = self.crear_usuario("administradora")
        self.operario = self.crear_usuario("operario")
        self.ajena = self.crear_usuario("ajena")
        self.finca = self.crear_finca(self.propietaria)
        self.finca_ajena = self.crear_finca(self.ajena)
        self.agregar_miembro(self.finca, self.administradora, Membresia.Rol.ADMINISTRADOR)
        self.agregar_miembro(self.finca, self.operario, Membresia.Rol.OPERARIO)

    def datos(self, finca=None):
        return {
            "finca": str((finca or self.finca).pk),
            "url_almacenamiento": "https://respaldos.example.com/finca/1.zip",
            "suma_verificacion": "a" * 64,
            "tamano_bytes": 2048,
            "version": "2026.01",
        }

    def test_propietaria_y_administradora_registran_respaldos(self):
        for usuario in (self.propietaria, self.administradora):
            self.autenticar(usuario)
            respuesta = self.client.post(reverse("backup-list"), self.datos(), format="json")
            self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
            self.assertEqual(respuesta.json()["creado_por"], str(usuario.pk))

    def test_el_operario_no_registra_ni_ve_respaldos(self):
        Respaldo.objects.create(
            finca=self.finca,
            creado_por=self.propietaria,
            url_almacenamiento="https://respaldos.example.com/finca/1.zip",
            suma_verificacion="b" * 64,
            tamano_bytes=1024,
            version="2026.01",
        )
        self.autenticar(self.operario)
        self.assertEqual(self.client.get(reverse("backup-list")).json()["count"], 0)
        respuesta = self.client.post(reverse("backup-list"), self.datos(), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("finca", respuesta.json())

    def test_no_se_registra_un_respaldo_de_otra_finca(self):
        self.autenticar(self.propietaria)
        respuesta = self.client.post(reverse("backup-list"), self.datos(self.finca_ajena), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Respaldo.objects.filter(finca=self.finca_ajena).exists())

    def test_los_respaldos_de_otras_fincas_son_invisibles(self):
        ajeno = Respaldo.objects.create(
            finca=self.finca_ajena,
            creado_por=self.ajena,
            url_almacenamiento="https://respaldos.example.com/ajena/1.zip",
            suma_verificacion="c" * 64,
            tamano_bytes=4096,
            version="2026.01",
        )
        self.autenticar(self.propietaria)
        self.assertEqual(self.client.get(reverse("backup-list")).json()["count"], 0)
        self.assertEqual(
            self.client.get(reverse("backup-detail", args=[ajeno.pk])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_los_respaldos_son_inmutables(self):
        self.autenticar(self.propietaria)
        creado = self.client.post(reverse("backup-list"), self.datos(), format="json").json()
        url = reverse("backup-detail", args=[creado["id"]])
        self.assertEqual(
            self.client.patch(url, {"version": "9999"}, format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_rechaza_un_respaldo_vacio(self):
        self.autenticar(self.propietaria)
        datos = self.datos()
        datos["tamano_bytes"] = 0
        respuesta = self.client.post(reverse("backup-list"), datos, format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
