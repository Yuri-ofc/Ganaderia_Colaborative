import shutil
import tempfile
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from apps.cattle.models import Bovino, Potrero, Raza
from apps.common.testing import PruebaApi
from apps.farms.models import Membresia
from apps.measurements.models import Medicion

from .models import CapturaVision
from .services import VERSION_SIMULADA


class PruebasCapturasVision(PruebaApi):
    def setUp(self):
        super().setUp()
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        ajustes = override_settings(MEDIA_ROOT=self.media)
        ajustes.enable()
        self.addCleanup(ajustes.disable)

        self.propietaria = self.crear_usuario("propietaria")
        self.operario = self.crear_usuario("operario")
        self.ajena = self.crear_usuario("ajena")
        self.finca = self.crear_finca(self.propietaria)
        self.finca_ajena = self.crear_finca(self.ajena)
        self.agregar_miembro(self.finca, self.operario, Membresia.Rol.OPERARIO)
        self.raza = Raza.objects.create(nombre="Brahman")
        self.potrero = Potrero.objects.create(finca=self.finca, nombre="Norte")
        self.bovino = self.crear_bovino(self.finca)
        self.bovino_ajeno = self.crear_bovino(
            self.finca_ajena, propietario=self.ajena, arete="AJ-1"
        )

    def crear_bovino(self, finca, propietario=None, arete="VIS-1"):
        potrero = (
            self.potrero if finca == self.finca
            else Potrero.objects.create(finca=finca, nombre="Sur")
        )
        return Bovino.objects.create(
            finca=finca, potrero=potrero, raza=self.raza, arete=arete,
            sexo=Bovino.Sexo.HEMBRA, categoria_productiva="Cría",
            creado_por=propietario or self.propietaria,
        )

    def archivo(self, nombre="captura.jpg", contenido=b"imagen-de-prueba"):
        return SimpleUploadedFile(nombre, contenido, content_type="image/jpeg")

    def subir(self, bovino=None, **extra):
        datos = {
            "bovino": str((bovino or self.bovino).pk),
            "tipo_archivo": "foto",
            "archivo": self.archivo(),
        }
        datos.update(extra)
        return self.client.post(reverse("vision-capture-list"), datos, format="multipart")

    def test_la_captura_genera_una_medicion_marcada_como_simulada(self):
        self.autenticar(self.operario)
        respuesta = self.subir()
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        cuerpo = respuesta.json()
        self.assertIsNotNone(cuerpo["medicion"])
        detalle = cuerpo["medicion_detalle"]
        self.assertEqual(detalle["bovino"], str(self.bovino.pk))
        medicion = Medicion.objects.get(pk=cuerpo["medicion"])
        self.assertEqual(medicion.modelo_ia.version, VERSION_SIMULADA)
        self.assertEqual(medicion.modo_captura, Medicion.ModoCaptura.FOTO)
        self.assertEqual(medicion.creado_por_id, self.operario.pk)

    def test_la_estimacion_respeta_las_restricciones_de_la_medicion(self):
        self.autenticar(self.operario)
        self.subir()
        medicion = Medicion.objects.get()
        self.assertGreater(medicion.peso_estimado_kg, Decimal("0"))
        self.assertLessEqual(medicion.intervalo_confianza_min_kg, medicion.peso_estimado_kg)
        self.assertLessEqual(medicion.peso_estimado_kg, medicion.intervalo_confianza_max_kg)
        self.assertGreaterEqual(medicion.intervalo_confianza_min_kg, Decimal("0"))
        self.assertGreater(medicion.condicion_corporal, Decimal("0"))
        self.assertTrue(Decimal("0") <= medicion.nivel_confianza <= Decimal("100"))

    def test_un_video_queda_registrado_con_su_modo_de_captura(self):
        self.autenticar(self.operario)
        respuesta = self.subir(
            tipo_archivo="video",
            archivo=self.archivo("captura.mp4", b"video-de-prueba"),
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Medicion.objects.get().modo_captura, Medicion.ModoCaptura.VIDEO)

    def test_las_capturas_reutilizan_un_solo_dispositivo_virtual(self):
        self.autenticar(self.operario)
        self.subir()
        self.subir()
        from apps.measurements.models import Dispositivo

        self.assertEqual(Dispositivo.objects.filter(propietario=self.operario).count(), 1)

    def test_no_se_sube_una_captura_de_un_bovino_ajeno(self):
        self.autenticar(self.operario)
        respuesta = self.subir(self.bovino_ajeno)
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(CapturaVision.objects.exists())

    def test_se_rechaza_un_archivo_demasiado_grande(self):
        self.autenticar(self.operario)
        with override_settings(VISION_TAMANO_MAXIMO_MB=0):
            respuesta = self.subir()
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("archivo", respuesta.json())
        self.assertFalse(Medicion.objects.exists())

    def test_las_capturas_de_otras_fincas_son_invisibles(self):
        self.autenticar(self.ajena)
        self.subir(self.bovino_ajeno)
        self.autenticar(self.operario)
        self.assertEqual(self.client.get(reverse("vision-capture-list")).json()["count"], 0)

    def test_sin_el_recurso_de_vision_no_hay_acceso(self):
        sin_permisos = self.crear_usuario("mirona", con_permisos_rbac=False)
        self.agregar_miembro(self.finca, sin_permisos, Membresia.Rol.OPERARIO)
        self.autenticar(sin_permisos)
        self.assertEqual(
            self.client.get(reverse("vision-capture-list")).status_code, status.HTTP_403_FORBIDDEN
        )

    def test_la_captura_es_inmutable(self):
        self.autenticar(self.operario)
        creada = self.subir().json()
        url = reverse("vision-capture-detail", args=[creada["id"]])
        self.assertEqual(
            self.client.patch(url, {"tipo_archivo": "video"}, format="multipart").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
