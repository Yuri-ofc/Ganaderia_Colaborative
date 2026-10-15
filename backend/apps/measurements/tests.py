from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.cattle.models import Bovino, Potrero, Raza
from apps.common.testing import PruebaApi
from apps.farms.models import Membresia

from .models import Dispositivo, Medicion, MedidaMorfometrica, ModeloIa, Pesaje, TipoMedida


class AyudasMediciones:
    def setUp(self):
        super().setUp()
        self.raza = Raza.objects.create(nombre="Brahman")
        self.modelo_ia = ModeloIa.objects.create(version="1.0", calibracion="base", activo=True)
        self.tipo_medida = TipoMedida.objects.create(nombre="Perímetro torácico", unidad="cm")

        self.propietaria = self.crear_usuario("propietaria")
        self.operaria = self.crear_usuario("operaria")
        self.finca = self.crear_finca(self.propietaria)
        self.agregar_miembro(self.finca, self.operaria, Membresia.Rol.OPERARIO)
        self.potrero = Potrero.objects.create(finca=self.finca, nombre="Potrero A")
        self.animal = Bovino.objects.create(
            finca=self.finca,
            potrero=self.potrero,
            arete="DEM-001",
            raza=self.raza,
            sexo=Bovino.Sexo.HEMBRA,
            categoria_productiva="Levante",
            creado_por=self.propietaria,
        )
        self.dispositivo = Dispositivo.objects.create(
            propietario=self.operaria, modelo="Movil", sistema_operativo="Android 14"
        )

        self.ajena = self.crear_usuario("ajena")
        self.finca_ajena = self.crear_finca(self.ajena)
        self.potrero_ajeno = Potrero.objects.create(finca=self.finca_ajena, nombre="Potrero B")
        self.animal_ajeno = Bovino.objects.create(
            finca=self.finca_ajena,
            potrero=self.potrero_ajeno,
            arete="AJE-001",
            raza=self.raza,
            sexo=Bovino.Sexo.MACHO,
            categoria_productiva="Ceba",
            creado_por=self.ajena,
        )
        self.dispositivo_ajeno = Dispositivo.objects.create(
            propietario=self.ajena, modelo="Tablet", sistema_operativo="Android 13"
        )

    def datos_medicion(self, **extra):
        datos = {
            "bovino": str(self.animal.pk),
            "dispositivo": str(self.dispositivo.pk),
            "modelo_ia": str(self.modelo_ia.pk),
            "capturado_en": timezone.now().isoformat(),
            "modo_captura": "video",
            "peso_estimado_kg": "420.50",
            "intervalo_confianza_min_kg": "410.00",
            "intervalo_confianza_max_kg": "430.00",
            "condicion_corporal": "3.5",
            "nivel_confianza": "92.40",
        }
        datos.update(extra)
        return datos

    def crear_medicion(self, **extra):
        valores = {
            "bovino": self.animal,
            "creado_por": self.operaria,
            "dispositivo": self.dispositivo,
            "modelo_ia": self.modelo_ia,
            "capturado_en": timezone.now(),
            "modo_captura": Medicion.ModoCaptura.VIDEO,
            "peso_estimado_kg": Decimal("420.50"),
            "intervalo_confianza_min_kg": Decimal("410.00"),
            "intervalo_confianza_max_kg": Decimal("430.00"),
            "condicion_corporal": Decimal("3.5"),
            "nivel_confianza": Decimal("92.40"),
        }
        return Medicion.objects.create(**{**valores, **extra})


class PruebasCreacionMediciones(AyudasMediciones, PruebaApi):
    def test_el_operario_registra_una_medicion(self):
        self.autenticar(self.operaria)
        respuesta = self.client.post(reverse("measurement-list"), self.datos_medicion(), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.json()["creado_por"], str(self.operaria.pk))

    def test_el_dispositivo_debe_ser_del_autor(self):
        self.autenticar(self.operaria)
        respuesta = self.client.post(
            reverse("measurement-list"),
            self.datos_medicion(dispositivo=str(self.dispositivo_ajeno.pk)),
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("dispositivo", respuesta.json())

    def test_no_se_mide_un_bovino_de_otra_finca(self):
        self.autenticar(self.operaria)
        respuesta = self.client.post(
            reverse("measurement-list"),
            self.datos_medicion(bovino=str(self.animal_ajeno.pk)),
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("bovino", respuesta.json())
        self.assertFalse(Medicion.objects.filter(bovino=self.animal_ajeno).exists())

    def test_valida_el_intervalo_de_confianza(self):
        self.autenticar(self.operaria)
        respuesta = self.client.post(
            reverse("measurement-list"),
            self.datos_medicion(
                intervalo_confianza_min_kg="430.00", intervalo_confianza_max_kg="425.00"
            ),
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rechaza_un_nivel_de_confianza_fuera_de_rango(self):
        self.autenticar(self.operaria)
        respuesta = self.client.post(
            reverse("measurement-list"), self.datos_medicion(nivel_confianza="140.00"), format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nivel_confianza", respuesta.json())

    def test_rechaza_un_modelo_de_ia_inactivo(self):
        retirado = ModeloIa.objects.create(version="0.9", calibracion="vieja", activo=False)
        self.autenticar(self.operaria)
        respuesta = self.client.post(
            reverse("measurement-list"), self.datos_medicion(modelo_ia=str(retirado.pk)), format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("modelo_ia", respuesta.json())


class PruebasInmutabilidad(AyudasMediciones, PruebaApi):
    def test_las_mediciones_no_se_editan_ni_se_borran(self):
        medicion = self.crear_medicion()
        url = reverse("measurement-detail", args=[medicion.pk])
        self.autenticar(self.propietaria)
        for metodo in (self.client.put, self.client.patch):
            respuesta = metodo(url, {"peso_estimado_kg": "1.00"}, format="json")
            self.assertEqual(respuesta.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        medicion.refresh_from_db()
        self.assertEqual(medicion.peso_estimado_kg, Decimal("420.50"))

    def test_una_correccion_es_una_medicion_nueva(self):
        original = self.crear_medicion()
        self.autenticar(self.operaria)
        respuesta = self.client.post(
            reverse("measurement-list"),
            self.datos_medicion(corrige=str(original.pk), peso_estimado_kg="425.00"),
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.json()["corrige"], str(original.pk))
        self.assertEqual(Medicion.objects.count(), 2)

    def test_la_correccion_apunta_al_mismo_bovino(self):
        ajena = self.crear_medicion(
            bovino=self.animal_ajeno, creado_por=self.ajena, dispositivo=self.dispositivo_ajeno
        )
        self.autenticar(self.operaria)
        respuesta = self.client.post(
            reverse("measurement-list"), self.datos_medicion(corrige=str(ajena.pk)), format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("corrige", respuesta.json())

    def test_los_pesajes_no_se_editan_ni_se_borran(self):
        pesaje = Pesaje.objects.create(
            bovino=self.animal,
            creado_por=self.operaria,
            pesado_en=timezone.now(),
            tipo_bascula="Báscula fija",
            peso_real_kg=Decimal("418.00"),
        )
        url = reverse("scale-weighing-detail", args=[pesaje.pk])
        self.autenticar(self.propietaria)
        self.assertEqual(
            self.client.patch(url, {"peso_real_kg": "1.00"}, format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        pesaje.refresh_from_db()
        self.assertEqual(pesaje.peso_real_kg, Decimal("418.00"))


class PruebasAislamientoMediciones(AyudasMediciones, PruebaApi):
    def test_las_listas_se_limitan_a_mis_fincas(self):
        propia = self.crear_medicion()
        ajena = self.crear_medicion(
            bovino=self.animal_ajeno, creado_por=self.ajena, dispositivo=self.dispositivo_ajeno
        )
        self.autenticar(self.operaria)
        ids = [item["id"] for item in self.client.get(reverse("measurement-list")).json()["results"]]
        self.assertEqual(ids, [str(propia.pk)])
        self.assertEqual(
            self.client.get(reverse("measurement-detail", args=[ajena.pk])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_los_pesajes_se_limitan_a_mis_fincas(self):
        ajeno = Pesaje.objects.create(
            bovino=self.animal_ajeno,
            creado_por=self.ajena,
            pesado_en=timezone.now(),
            tipo_bascula="Báscula",
            peso_real_kg=Decimal("300.00"),
        )
        self.autenticar(self.operaria)
        self.assertEqual(self.client.get(reverse("scale-weighing-list")).json()["count"], 0)
        self.assertEqual(
            self.client.get(reverse("scale-weighing-detail", args=[ajeno.pk])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_los_dispositivos_son_privados_de_su_propietario(self):
        self.autenticar(self.operaria)
        cuerpo = self.client.get(reverse("device-list")).json()
        self.assertEqual([item["id"] for item in cuerpo["results"]], [str(self.dispositivo.pk)])
        self.assertEqual(
            self.client.get(reverse("device-detail", args=[self.dispositivo_ajeno.pk])).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_las_morfometricas_siguen_el_alcance_de_la_medicion(self):
        propia = self.crear_medicion()
        ajena = self.crear_medicion(
            bovino=self.animal_ajeno, creado_por=self.ajena, dispositivo=self.dispositivo_ajeno
        )
        MedidaMorfometrica.objects.create(
            medicion=ajena, tipo_medida=self.tipo_medida, valor=Decimal("170.00")
        )
        self.autenticar(self.operaria)
        self.assertEqual(self.client.get(reverse("morphometric-measurement-list")).json()["count"], 0)

        respuesta = self.client.post(
            reverse("morphometric-measurement-list"),
            {
                "medicion": str(propia.pk),
                "tipo_medida": str(self.tipo_medida.pk),
                "valor": "185.50",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

        repetida = self.client.post(
            reverse("morphometric-measurement-list"),
            {
                "medicion": str(propia.pk),
                "tipo_medida": str(self.tipo_medida.pk),
                "valor": "186.00",
            },
            format="json",
        )
        self.assertEqual(repetida.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tipo_medida", repetida.json())


class PruebasCatalogosCompartidos(AyudasMediciones, PruebaApi):
    def test_solo_el_personal_edita_los_catalogos(self):
        self.autenticar(self.propietaria)
        self.assertEqual(
            self.client.post(
                reverse("measurement-type-list"), {"nombre": "Altura", "unidad": "cm"}, format="json"
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.post(
                reverse("ai-model-list"), {"version": "2.0", "calibracion": "nueva"}, format="json"
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )

        personal = self.crear_usuario("tecnico", is_staff=True)
        self.autenticar(personal)
        self.assertEqual(
            self.client.post(
                reverse("measurement-type-list"), {"nombre": "Altura", "unidad": "cm"}, format="json"
            ).status_code,
            status.HTTP_201_CREATED,
        )
