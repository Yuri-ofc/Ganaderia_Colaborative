from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from rest_framework import status

from apps.backups.models import Respaldo
from apps.cattle.models import Bovino, MovimientoPotrero, Potrero, Raza
from apps.common.testing import PruebaApi
from apps.farms.models import Finca, Invitacion, Membresia
from apps.measurements.models import (
    Dispositivo,
    Medicion,
    MedidaMorfometrica,
    ModeloIa,
    Pesaje,
    TipoMedida,
)
from apps.sync.models import CambioSincronizacion
from config import env

Usuario = get_user_model()

MODELOS_DE_NEGOCIO = (
    Usuario,
    Finca,
    Membresia,
    Invitacion,
    Raza,
    Potrero,
    Bovino,
    MovimientoPotrero,
    Dispositivo,
    ModeloIa,
    TipoMedida,
    Medicion,
    MedidaMorfometrica,
    Pesaje,
    Respaldo,
    CambioSincronizacion,
)


def conteos_de_negocio():
    return {modelo._meta.db_table: modelo.objects.count() for modelo in MODELOS_DE_NEGOCIO}


class PruebasRaizApi(PruebaApi):
    def test_la_raiz_lista_todas_las_rutas_en_json(self):
        respuesta = self.client.get(reverse("api-root"))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta["Content-Type"], "application/json")
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["version"], "v1")
        self.assertIn("farms", cuerpo["endpoints"])
        self.assertTrue(cuerpo["endpoints"]["measurements"].endswith("/api/v1/measurements/"))
        self.assertTrue(cuerpo["endpoints"]["token"].endswith("/api/v1/auth/token/"))
        self.assertEqual(len(cuerpo["endpoints"]), 18)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class PruebasComandoSeedDemo(TestCase):
    def sembrar(self, *args):
        salida = StringIO()
        call_command("seed_demo", *args, stdout=salida)
        return salida.getvalue()

    def test_crea_exactamente_cien_registros_de_negocio(self):
        antes = conteos_de_negocio()
        self.sembrar()
        despues = conteos_de_negocio()
        creados = {
            tabla: despues[tabla] - antes[tabla]
            for tabla in despues
            if despues[tabla] != antes[tabla]
        }
        self.assertEqual(sum(creados.values()), 100)
        self.assertEqual(
            creados,
            {
                "accounts_usuario": 6,
                "farms_finca": 3,
                "farms_membresia": 6,
                "cattle_raza": 4,
                "cattle_potrero": 6,
                "cattle_bovino": 24,
                "measurements_dispositivo": 5,
                "measurements_modeloia": 2,
                "measurements_tipomedida": 4,
                "measurements_medicion": 20,
                "measurements_medidamorfometrica": 12,
                "measurements_pesaje": 8,
            },
        )

    def test_es_idempotente(self):
        self.sembrar()
        instantanea = conteos_de_negocio()
        salida = self.sembrar()
        self.assertEqual(conteos_de_negocio(), instantanea)
        self.assertIn("ya existían", salida)

    def test_no_toca_los_registros_previos(self):
        previa = Usuario.objects.create_user(username="usuaria_previa", password="x")
        finca = Finca.objects.create(propietario=previa, nombre="Finca Previa")
        self.sembrar()
        previa.refresh_from_db()
        finca.refresh_from_db()
        self.assertEqual(previa.username, "usuaria_previa")
        self.assertEqual(finca.nombre, "Finca Previa")
        self.assertEqual(Usuario.objects.count(), 7)

    def test_la_simulacion_no_guarda_nada(self):
        antes = conteos_de_negocio()
        salida = self.sembrar("--dry-run")
        self.assertEqual(conteos_de_negocio(), antes)
        self.assertIn("Simulación", salida)

    def test_los_datos_sembrados_respetan_las_reglas_de_acceso(self):
        self.sembrar()
        for animal in Bovino.objects.select_related("finca", "potrero").all():
            self.assertEqual(animal.potrero.finca_id, animal.finca_id)
        for medicion in Medicion.objects.select_related("bovino", "dispositivo").all():
            self.assertEqual(medicion.dispositivo.propietario_id, medicion.creado_por_id)
            tiene_acceso = Finca.objects.filter(
                pk=medicion.bovino.finca_id, propietario=medicion.creado_por
            ).exists() or Membresia.objects.filter(
                finca_id=medicion.bovino.finca_id,
                usuario=medicion.creado_por,
                eliminado_en__isnull=True,
            ).exists()
            self.assertTrue(tiene_acceso, f"{medicion.creado_por} no pertenece a la finca medida")


class PruebasLectorEnv(SimpleTestCase):
    def test_lee_valores_y_respeta_el_entorno_del_proceso(self):
        import os

        with TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / ".env"
            ruta.write_text(
                "\n".join(
                    [
                        "# comentario",
                        "",
                        "PRUEBA_TEXTO='valor citado'",
                        'PRUEBA_LISTA="uno, dos , tres"',
                        "export PRUEBA_EXPORT=con-export",
                        "PRUEBA_BOOL=si",
                        "PRUEBA_ENTERO=42",
                        "PRUEBA_YA_DEFINIDA=del-archivo",
                        "linea sin igual",
                    ]
                ),
                encoding="utf-8",
            )
            os.environ["PRUEBA_YA_DEFINIDA"] = "del-entorno"
            try:
                cargado = env.cargar_env(Path(carpeta) / "no-existe", ruta)
                self.assertEqual(cargado, ruta)
                self.assertEqual(env.leer_texto("PRUEBA_TEXTO"), "valor citado")
                self.assertEqual(env.leer_lista("PRUEBA_LISTA"), ["uno", "dos", "tres"])
                self.assertEqual(env.leer_texto("PRUEBA_EXPORT"), "con-export")
                self.assertTrue(env.leer_bool("PRUEBA_BOOL"))
                self.assertEqual(env.leer_entero("PRUEBA_ENTERO"), 42)
                self.assertEqual(env.leer_texto("PRUEBA_YA_DEFINIDA"), "del-entorno")
            finally:
                for clave in (
                    "PRUEBA_TEXTO",
                    "PRUEBA_LISTA",
                    "PRUEBA_EXPORT",
                    "PRUEBA_BOOL",
                    "PRUEBA_ENTERO",
                    "PRUEBA_YA_DEFINIDA",
                ):
                    os.environ.pop(clave, None)

    def test_valores_por_omision_y_faltantes(self):
        self.assertEqual(env.leer_texto("VARIABLE_INEXISTENTE", "defecto"), "defecto")
        self.assertFalse(env.leer_bool("VARIABLE_INEXISTENTE", False))
        self.assertEqual(env.leer_entero("VARIABLE_INEXISTENTE", 7), 7)
        with self.assertRaises(ImproperlyConfigured):
            env.leer_texto("VARIABLE_INEXISTENTE")

    def test_rechaza_valores_mal_formados(self):
        import os

        os.environ["PRUEBA_MALA"] = "quizás"
        try:
            with self.assertRaises(ImproperlyConfigured):
                env.leer_bool("PRUEBA_MALA")
            with self.assertRaises(ImproperlyConfigured):
                env.leer_entero("PRUEBA_MALA")
        finally:
            os.environ.pop("PRUEBA_MALA", None)

    def test_las_rutas_relativas_se_resuelven_contra_una_base(self):
        import os

        os.environ["PRUEBA_RUTA"] = "database/data/db.sqlite3"
        try:
            resuelta = env.leer_ruta("PRUEBA_RUTA", relativa_a="/srv/app")
            self.assertEqual(str(resuelta), "/srv/app/database/data/db.sqlite3")
        finally:
            os.environ.pop("PRUEBA_RUTA", None)


class PruebasAjustesDesdeEnv(SimpleTestCase):
    def test_los_ajustes_sensibles_vienen_del_entorno(self):
        from django.conf import settings

        self.assertEqual(Path(settings.DATABASE_NAME).name, "db.sqlite3")
        self.assertEqual(Path(settings.DATABASE_NAME).parent, Path(settings.DATABASE_DATA_DIR))
        self.assertEqual(settings.DATABASE_ENGINE, "django.db.backends.sqlite3")
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.Usuario")
        self.assertIn(
            "rest_framework.authentication.TokenAuthentication",
            settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"],
        )
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"],
            ["apps.common.permissions.PermisoUsuarioActivo"],
        )
