import shutil
import tempfile
from pathlib import Path

from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from apps.cattle.models import Bovino, Potrero, Raza
from apps.common.testing import PruebaApi
from apps.farms.models import Membresia

from .models import Respaldo
from .services import verificar_integridad


class BaseRespaldos(PruebaApi):
    """Cada prueba escribe sus archivos en un directorio propio y temporal."""

    def setUp(self):
        super().setUp()
        self.directorio = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.directorio, ignore_errors=True)
        ajustes = override_settings(RESPALDOS_DIR=self.directorio, RESPALDO_CLAVE_CIFRADO="")
        ajustes.enable()
        self.addCleanup(ajustes.disable)

        self.propietaria = self.crear_usuario("propietaria")
        self.administradora = self.crear_usuario("administradora")
        self.operario = self.crear_usuario("operario")
        self.ajena = self.crear_usuario("ajena")
        self.finca = self.crear_finca(self.propietaria)
        self.finca_ajena = self.crear_finca(self.ajena)
        self.agregar_miembro(self.finca, self.administradora, Membresia.Rol.ADMINISTRADOR)
        self.agregar_miembro(self.finca, self.operario, Membresia.Rol.OPERARIO)

    def datos(self, finca=None):
        return {"finca": str((finca or self.finca).pk)}

    def generar(self, finca=None):
        respuesta = self.client.post(reverse("backup-list"), self.datos(finca), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        return respuesta.json()

    def crear_bovino(self, arete):
        raza, _ = Raza.objects.get_or_create(nombre="Criollo")
        potrero, _ = Potrero.objects.get_or_create(finca=self.finca, nombre="Norte")
        return Bovino.objects.create(
            finca=self.finca, potrero=potrero, raza=raza, arete=arete,
            sexo=Bovino.Sexo.HEMBRA, categoria_productiva="Cría", creado_por=self.propietaria,
        )


class PruebasAccesoRespaldos(BaseRespaldos):
    def test_solo_la_propietaria_genera_respaldos(self):
        self.autenticar(self.propietaria)
        cuerpo = self.generar()
        self.assertEqual(cuerpo["creado_por"], str(self.propietaria.pk))

        self.autenticar(self.administradora)
        respuesta = self.client.post(reverse("backup-list"), self.datos(), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Respaldo.objects.filter(finca=self.finca).count(), 1)

    def test_el_operario_no_genera_ni_ve_respaldos(self):
        self.autenticar(self.propietaria)
        self.generar()
        self.autenticar(self.operario)
        self.assertEqual(self.client.get(reverse("backup-list")).status_code, status.HTTP_403_FORBIDDEN)
        respuesta = self.client.post(reverse("backup-list"), self.datos(), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_se_genera_un_respaldo_de_otra_finca(self):
        self.autenticar(self.propietaria)
        respuesta = self.client.post(reverse("backup-list"), self.datos(self.finca_ajena), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Respaldo.objects.filter(finca=self.finca_ajena).exists())

    def test_los_respaldos_de_otras_fincas_son_invisibles(self):
        self.autenticar(self.ajena)
        ajeno = self.generar(self.finca_ajena)
        self.autenticar(self.propietaria)
        self.assertEqual(self.client.get(reverse("backup-list")).json()["count"], 0)
        self.assertEqual(
            self.client.get(reverse("backup-detail", args=[ajeno["id"]])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_los_respaldos_son_inmutables(self):
        self.autenticar(self.propietaria)
        creado = self.generar()
        url = reverse("backup-detail", args=[creado["id"]])
        self.assertEqual(
            self.client.patch(url, {"version": "9999"}, format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class PruebasGeneracionDeRespaldos(BaseRespaldos):
    def test_el_servidor_calcula_tamano_y_suma_de_verificacion(self):
        self.crear_bovino("B-1")
        self.autenticar(self.propietaria)
        cuerpo = self.generar()
        self.assertGreater(cuerpo["tamano_bytes"], 0)
        self.assertEqual(len(cuerpo["suma_verificacion"]), 64)
        self.assertTrue(cuerpo["integridad_verificada"])
        self.assertIn("/download/", cuerpo["url_almacenamiento"])
        respaldo = Respaldo.objects.get(pk=cuerpo["id"])
        self.assertTrue((self.directorio / respaldo.ruta_relativa).is_file())

    def test_el_cliente_no_puede_falsear_la_integridad(self):
        self.autenticar(self.propietaria)
        respuesta = self.client.post(
            reverse("backup-list"),
            {**self.datos(), "suma_verificacion": "0" * 64, "tamano_bytes": 999999,
             "url_almacenamiento": "https://falso.example.com/x.zip"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        cuerpo = respuesta.json()
        self.assertNotEqual(cuerpo["suma_verificacion"], "0" * 64)
        self.assertNotEqual(cuerpo["tamano_bytes"], 999999)
        self.assertTrue(verificar_integridad(Respaldo.objects.get(pk=cuerpo["id"])))

    def test_descarga_el_archivo_del_respaldo(self):
        self.crear_bovino("B-2")
        self.autenticar(self.propietaria)
        creado = self.generar()
        respuesta = self.client.get(reverse("backup-download", args=[creado["id"]]))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn("attachment", respuesta["Content-Disposition"])
        self.assertIn(b"B-2", respuesta.content)

    def test_un_archivo_alterado_no_se_descarga(self):
        self.autenticar(self.propietaria)
        creado = self.generar()
        respaldo = Respaldo.objects.get(pk=creado["id"])
        (self.directorio / respaldo.ruta_relativa).write_bytes(b"[]")
        respuesta = self.client.get(reverse("backup-download", args=[creado["id"]]))
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(verificar_integridad(respaldo))

    def test_pedir_cifrado_sin_clave_configurada_falla_sin_guardar_en_claro(self):
        self.autenticar(self.propietaria)
        respuesta = self.client.post(
            reverse("backup-list"), {**self.datos(), "cifrado": True}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cifrado", respuesta.json())
        self.assertFalse(Respaldo.objects.exists())

    def test_con_clave_configurada_el_archivo_queda_cifrado(self):
        from cryptography.fernet import Fernet

        self.crear_bovino("B-3")
        with override_settings(RESPALDO_CLAVE_CIFRADO=Fernet.generate_key().decode()):
            self.autenticar(self.propietaria)
            creado = self.client.post(
                reverse("backup-list"), {**self.datos(), "cifrado": True}, format="json"
            ).json()
            respaldo = Respaldo.objects.get(pk=creado["id"])
            self.assertTrue(respaldo.cifrado)
            self.assertNotIn(b"B-3", (self.directorio / respaldo.ruta_relativa).read_bytes())
            self.assertTrue(verificar_integridad(respaldo))


class PruebasRestauracion(BaseRespaldos):
    def test_restaurar_devuelve_la_finca_al_estado_del_respaldo(self):
        self.crear_bovino("ANTES-1")
        self.autenticar(self.propietaria)
        creado = self.generar()
        self.crear_bovino("DESPUES-1")
        self.assertEqual(Bovino.objects.filter(finca=self.finca).count(), 2)

        respuesta = self.client.post(
            reverse("backup-restore", args=[creado["id"]]), {"confirmar": True}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        aretes = set(Bovino.objects.filter(finca=self.finca).values_list("arete", flat=True))
        self.assertEqual(aretes, {"ANTES-1"})
        self.assertEqual(respuesta.json()["restaurado"]["bovino"], 1)

    def test_restaurar_exige_confirmacion_explicita(self):
        self.crear_bovino("ANTES-2")
        self.autenticar(self.propietaria)
        creado = self.generar()
        self.crear_bovino("DESPUES-2")
        respuesta = self.client.post(
            reverse("backup-restore", args=[creado["id"]]), {}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirmar", respuesta.json())
        self.assertEqual(Bovino.objects.filter(finca=self.finca).count(), 2)

    def test_no_se_restaura_un_respaldo_alterado(self):
        self.crear_bovino("ANTES-3")
        self.autenticar(self.propietaria)
        creado = self.generar()
        respaldo = Respaldo.objects.get(pk=creado["id"])
        (self.directorio / respaldo.ruta_relativa).write_bytes(b"[]")
        self.crear_bovino("DESPUES-3")
        respuesta = self.client.post(
            reverse("backup-restore", args=[creado["id"]]), {"confirmar": True}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Bovino.objects.filter(finca=self.finca).count(), 2)

    def test_la_administradora_no_restaura(self):
        self.autenticar(self.propietaria)
        creado = self.generar()
        self.autenticar(self.administradora)
        respuesta = self.client.post(
            reverse("backup-restore", args=[creado["id"]]), {"confirmar": True}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)


class PruebasExportaciones(BaseRespaldos):
    def test_exporta_un_conjunto_en_csv(self):
        self.crear_bovino("EXP-1")
        self.autenticar(self.propietaria)
        respuesta = self.client.get(
            reverse("export-list"), {"finca": str(self.finca.pk), "incluir": "bovinos", "formato": "csv"}
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn("text/csv", respuesta["Content-Type"])
        self.assertIn("arete", respuesta.content.decode())
        self.assertIn("EXP-1", respuesta.content.decode())

    def test_varios_conjuntos_en_csv_llegan_comprimidos(self):
        self.crear_bovino("EXP-2")
        self.autenticar(self.propietaria)
        respuesta = self.client.get(
            reverse("export-list"),
            {"finca": str(self.finca.pk), "incluir": "bovinos,pesajes", "formato": "csv"},
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta["Content-Type"], "application/zip")

    def test_exporta_en_json(self):
        self.crear_bovino("EXP-3")
        self.autenticar(self.propietaria)
        respuesta = self.client.get(
            reverse("export-list"), {"finca": str(self.finca.pk), "incluir": "bovinos", "formato": "json"}
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["bovinos"][0]["arete"], "EXP-3")

    def test_no_se_exporta_una_finca_ajena(self):
        self.autenticar(self.propietaria)
        respuesta = self.client.get(
            reverse("export-list"), {"finca": str(self.finca_ajena.pk), "incluir": "bovinos"}
        )
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_rechaza_un_formato_desconocido(self):
        self.autenticar(self.propietaria)
        respuesta = self.client.get(
            reverse("export-list"), {"finca": str(self.finca.pk), "incluir": "bovinos", "formato": "xls"}
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
