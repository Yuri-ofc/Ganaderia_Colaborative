import uuid

from django.urls import reverse
from rest_framework import status

from apps.common.testing import PruebaApi
from apps.farms.models import Membresia
from apps.measurements.models import Dispositivo

from .models import CambioSincronizacion


class PruebasCambiosSincronizacion(PruebaApi):
    def setUp(self):
        super().setUp()
        self.propietaria = self.crear_usuario("propietaria")
        self.operario = self.crear_usuario("operario")
        self.ajena = self.crear_usuario("ajena")
        self.finca = self.crear_finca(self.propietaria)
        self.finca_ajena = self.crear_finca(self.ajena)
        self.agregar_miembro(self.finca, self.operario, Membresia.Rol.OPERARIO)
        self.dispositivo = Dispositivo.objects.create(
            propietario=self.operario, modelo="Movil", sistema_operativo="Android 14"
        )
        self.dispositivo_ajeno = Dispositivo.objects.create(
            propietario=self.ajena, modelo="Tablet", sistema_operativo="Android 13"
        )

    def datos(self, **extra):
        valores = {
            "finca": str(self.finca.pk),
            "dispositivo": str(self.dispositivo.pk),
            "id_cambio_cliente": str(uuid.uuid4()),
            "recurso": "bovino",
            "id_objeto": str(uuid.uuid4()),
            "accion": "crear",
            "contenido": {"arete": "DEM-001"},
        }
        valores.update(extra)
        return valores

    def test_el_operario_sube_un_cambio_de_su_dispositivo(self):
        self.autenticar(self.operario)
        respuesta = self.client.post(reverse("sync-change-list"), self.datos(), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["creado_por"], str(self.operario.pk))
        self.assertIsNone(cuerpo["sincronizado_en"])

    def test_no_se_suben_cambios_de_otra_finca(self):
        self.autenticar(self.operario)
        respuesta = self.client.post(
            reverse("sync-change-list"), self.datos(finca=str(self.finca_ajena.pk)), format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("finca", respuesta.json())

    def test_no_se_suben_cambios_desde_un_dispositivo_ajeno(self):
        self.autenticar(self.operario)
        respuesta = self.client.post(
            reverse("sync-change-list"), self.datos(dispositivo=str(self.dispositivo_ajeno.pk)), format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("dispositivo", respuesta.json())

    def test_el_mismo_cambio_no_se_duplica(self):
        self.autenticar(self.operario)
        datos = self.datos()
        self.assertEqual(
            self.client.post(reverse("sync-change-list"), datos, format="json").status_code,
            status.HTTP_201_CREATED,
        )
        repetido = self.client.post(reverse("sync-change-list"), datos, format="json")
        self.assertEqual(repetido.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("id_cambio_cliente", str(repetido.json()))
        self.assertEqual(CambioSincronizacion.objects.count(), 1)

    def test_solo_el_propietario_del_dispositivo_confirma(self):
        cambio = CambioSincronizacion.objects.create(
            finca=self.finca,
            dispositivo=self.dispositivo,
            creado_por=self.operario,
            id_cambio_cliente=uuid.uuid4(),
            recurso="bovino",
            id_objeto=uuid.uuid4(),
            accion=CambioSincronizacion.Accion.CREAR,
        )
        url = reverse("sync-change-acknowledge", args=[cambio.pk])

        self.autenticar(self.propietaria)
        self.assertEqual(self.client.post(url).status_code, status.HTTP_403_FORBIDDEN)

        self.autenticar(self.operario)
        respuesta = self.client.post(url)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        cambio.refresh_from_db()
        self.assertIsNotNone(cambio.sincronizado_en)

    def test_los_cambios_de_otras_fincas_son_invisibles(self):
        ajeno = CambioSincronizacion.objects.create(
            finca=self.finca_ajena,
            dispositivo=self.dispositivo_ajeno,
            creado_por=self.ajena,
            id_cambio_cliente=uuid.uuid4(),
            recurso="bovino",
            id_objeto=uuid.uuid4(),
            accion=CambioSincronizacion.Accion.ACTUALIZAR,
        )
        self.autenticar(self.operario)
        self.assertEqual(self.client.get(reverse("sync-change-list")).json()["count"], 0)
        self.assertEqual(
            self.client.get(reverse("sync-change-detail", args=[ajeno.pk])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_los_cambios_subidos_son_inmutables(self):
        self.autenticar(self.operario)
        creado = self.client.post(reverse("sync-change-list"), self.datos(), format="json").json()
        url = reverse("sync-change-detail", args=[creado["id"]])
        self.assertEqual(
            self.client.patch(url, {"recurso": "otro"}, format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
