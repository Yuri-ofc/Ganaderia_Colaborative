from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.common.testing import PruebaApi
from apps.farms.models import Membresia

from .models import Bovino, MovimientoPotrero, Potrero, Raza


class AyudasBovinos:
    def crear_finca_con_bovino(self, nombre_propietario, arete="DEM-001"):
        propietario = self.crear_usuario(nombre_propietario)
        finca = self.crear_finca(propietario)
        potrero = Potrero.objects.create(finca=finca, nombre="Potrero Único")
        animal = Bovino.objects.create(
            finca=finca,
            potrero=potrero,
            arete=arete,
            raza=self.raza,
            sexo=Bovino.Sexo.HEMBRA,
            categoria_productiva="Levante",
            creado_por=propietario,
        )
        return propietario, finca, potrero, animal


class PruebasAislamientoBovinos(AyudasBovinos, PruebaApi):
    def setUp(self):
        super().setUp()
        self.raza = Raza.objects.create(nombre="Brahman")
        self.propietaria, self.finca, self.potrero, self.animal = self.crear_finca_con_bovino("propietaria")
        self.vecina, self.finca_vecina, self.potrero_vecino, self.animal_vecino = (
            self.crear_finca_con_bovino("vecina", arete="AJE-001")
        )
        self.operaria = self.crear_usuario("operaria")
        self.agregar_miembro(self.finca, self.operaria, Membresia.Rol.OPERARIO)

    def test_la_lista_solo_muestra_bovinos_de_mis_fincas(self):
        self.autenticar(self.propietaria)
        cuerpo = self.client.get(reverse("cattle-list")).json()
        self.assertEqual([item["id"] for item in cuerpo["results"]], [str(self.animal.pk)])

    def test_no_se_puede_consultar_un_bovino_ajeno(self):
        self.autenticar(self.propietaria)
        respuesta = self.client.get(reverse("cattle-detail", args=[self.animal_vecino.pk]))
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_no_se_puede_registrar_en_una_finca_ajena(self):
        self.autenticar(self.propietaria)
        respuesta = self.client.post(
            reverse("cattle-list"),
            {
                "finca": str(self.finca_vecina.pk),
                "potrero": str(self.potrero_vecino.pk),
                "arete": "INTRUSO-1",
                "raza": str(self.raza.pk),
                "sexo": "hembra",
                "categoria_productiva": "Ceba",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("finca", respuesta.json())
        self.assertFalse(Bovino.objects.filter(arete="INTRUSO-1").exists())

    def test_el_potrero_debe_ser_de_la_misma_finca(self):
        self.autenticar(self.propietaria)
        potrero_ajeno = Potrero.objects.create(finca=self.finca_vecina, nombre="Potrero Vecino")
        respuesta = self.client.post(
            reverse("cattle-list"),
            {
                "finca": str(self.finca.pk),
                "potrero": str(potrero_ajeno.pk),
                "arete": "DEM-002",
                "raza": str(self.raza.pk),
                "sexo": "macho",
                "categoria_productiva": "Ceba",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("potrero", respuesta.json())

    def test_el_operario_registra_bovinos_y_queda_como_autor(self):
        self.autenticar(self.operaria)
        respuesta = self.client.post(
            reverse("cattle-list"),
            {
                "finca": str(self.finca.pk),
                "potrero": str(self.potrero.pk),
                "arete": "DEM-010",
                "raza": str(self.raza.pk),
                "sexo": "hembra",
                "categoria_productiva": "Cría",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["creado_por"], str(self.operaria.pk))
        self.assertEqual(cuerpo["estado_operativo"], Bovino.EstadoOperativo.PERFIL_PENDIENTE)

    def test_el_arete_es_unico_por_finca_pero_reutilizable_entre_fincas(self):
        self.autenticar(self.propietaria)
        repetido = self.client.post(
            reverse("cattle-list"),
            {
                "finca": str(self.finca.pk),
                "potrero": str(self.potrero.pk),
                "arete": self.animal.arete,
                "raza": str(self.raza.pk),
                "sexo": "macho",
                "categoria_productiva": "Ceba",
            },
            format="json",
        )
        self.assertEqual(repetido.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("arete", repetido.json())

        self.autenticar(self.vecina)
        aceptado = self.client.post(
            reverse("cattle-list"),
            {
                "finca": str(self.finca_vecina.pk),
                "potrero": str(self.potrero_vecino.pk),
                "arete": self.animal.arete,
                "raza": str(self.raza.pk),
                "sexo": "macho",
                "categoria_productiva": "Ceba",
            },
            format="json",
        )
        self.assertEqual(aceptado.status_code, status.HTTP_201_CREATED)

    def test_rechaza_una_fecha_de_nacimiento_futura(self):
        self.autenticar(self.propietaria)
        respuesta = self.client.post(
            reverse("cattle-list"),
            {
                "finca": str(self.finca.pk),
                "potrero": str(self.potrero.pk),
                "arete": "DEM-050",
                "raza": str(self.raza.pk),
                "sexo": "hembra",
                "categoria_productiva": "Cría",
                "fecha_nacimiento_estimada": (timezone.localdate() + timezone.timedelta(days=1)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fecha_nacimiento_estimada", respuesta.json())

    def test_el_operario_no_elimina_bovinos(self):
        self.autenticar(self.operaria)
        respuesta = self.client.delete(reverse("cattle-detail", args=[self.animal.pk]))
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.animal.refresh_from_db()
        self.assertIsNone(self.animal.eliminado_en)


class PruebasCicloVidaBovino(AyudasBovinos, PruebaApi):
    def setUp(self):
        super().setUp()
        self.raza = Raza.objects.create(nombre="Gyr")
        self.ganadera, self.finca, self.potrero, self.animal = self.crear_finca_con_bovino("ganadera")
        self.peon = self.crear_usuario("peon")
        self.agregar_miembro(self.finca, self.peon, Membresia.Rol.OPERARIO)

    def test_aprobar_el_perfil_activa_al_animal(self):
        self.autenticar(self.ganadera)
        respuesta = self.client.post(reverse("cattle-approve-profile", args=[self.animal.pk]))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.animal.refresh_from_db()
        self.assertEqual(self.animal.estado_operativo, Bovino.EstadoOperativo.ACTIVO)
        self.assertEqual(self.animal.perfil_aprobado_por, self.ganadera)

    def test_el_operario_no_aprueba_perfiles(self):
        self.autenticar(self.peon)
        respuesta = self.client.post(reverse("cattle-approve-profile", args=[self.animal.pk]))
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_la_baja_exige_motivo_y_estado_valido(self):
        self.autenticar(self.ganadera)
        self.assertEqual(
            self.client.post(
                reverse("cattle-deactivate", args=[self.animal.pk]), {"estado": "activo"}, format="json"
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.client.post(
                reverse("cattle-deactivate", args=[self.animal.pk]),
                {"estado": "vendido", "motivo": "   "},
                format="json",
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        respuesta = self.client.post(
            reverse("cattle-deactivate", args=[self.animal.pk]),
            {"estado": "vendido", "motivo": "Venta en feria"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.animal.refresh_from_db()
        self.assertEqual(self.animal.estado_operativo, Bovino.EstadoOperativo.VENDIDO)
        self.assertEqual(self.animal.motivo_desactivacion, "Venta en feria")
        self.assertIsNotNone(self.animal.desactivado_en)
        self.assertEqual(
            self.client.post(
                reverse("cattle-deactivate", args=[self.animal.pk]),
                {"estado": "muerto", "motivo": "Otra vez"},
                format="json",
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )


class PruebasPotrerosYMovimientos(AyudasBovinos, PruebaApi):
    def setUp(self):
        super().setUp()
        self.raza = Raza.objects.create(nombre="Normando")
        self.mayordoma, self.finca, self.potrero, self.animal = self.crear_finca_con_bovino("mayordoma")
        self.vaquero = self.crear_usuario("vaquero")
        self.agregar_miembro(self.finca, self.vaquero, Membresia.Rol.OPERARIO)
        self.extrana, self.finca_extrana, self.potrero_extrano, self.animal_extrano = (
            self.crear_finca_con_bovino("extrana", arete="EXT-001")
        )

    def test_el_operario_no_crea_potreros(self):
        self.autenticar(self.vaquero)
        respuesta = self.client.post(
            reverse("lot-list"), {"finca": str(self.finca.pk), "nombre": "Potrero Nuevo"}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("finca", respuesta.json())

    def test_los_nombres_de_potrero_son_unicos_por_finca(self):
        self.autenticar(self.mayordoma)
        respuesta = self.client.post(
            reverse("lot-list"), {"finca": str(self.finca.pk), "nombre": self.potrero.nombre}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nombre", respuesta.json())

    def test_no_se_elimina_un_potrero_con_bovinos_activos(self):
        self.autenticar(self.mayordoma)
        respuesta = self.client.delete(reverse("lot-detail", args=[self.potrero.pk]))
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_los_potreros_de_otras_fincas_son_invisibles(self):
        self.autenticar(self.mayordoma)
        cuerpo = self.client.get(reverse("lot-list")).json()
        self.assertEqual([item["id"] for item in cuerpo["results"]], [str(self.potrero.pk)])

    def test_el_movimiento_actualiza_el_potrero_actual(self):
        self.autenticar(self.mayordoma)
        destino = Potrero.objects.create(finca=self.finca, nombre="Potrero Destino")
        respuesta = self.client.post(
            reverse("lot-movement-list"),
            {
                "bovino": str(self.animal.pk),
                "potrero": str(destino.pk),
                "iniciado_en": timezone.now().isoformat(),
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.animal.refresh_from_db()
        self.assertEqual(self.animal.potrero, destino)

    def test_el_potrero_del_movimiento_debe_ser_de_la_finca_del_bovino(self):
        self.autenticar(self.mayordoma)
        respuesta = self.client.post(
            reverse("lot-movement-list"),
            {
                "bovino": str(self.animal.pk),
                "potrero": str(self.potrero_extrano.pk),
                "iniciado_en": timezone.now().isoformat(),
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_los_movimientos_no_se_eliminan(self):
        self.autenticar(self.mayordoma)
        movimiento = MovimientoPotrero.objects.create(
            bovino=self.animal, potrero=self.potrero, iniciado_en=timezone.now(), creado_por=self.mayordoma
        )
        respuesta = self.client.delete(reverse("lot-movement-detail", args=[movimiento.pk]))
        self.assertEqual(respuesta.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class PruebasCatalogoRazas(PruebaApi):
    def setUp(self):
        super().setUp()
        self.raza = Raza.objects.create(nombre="Holstein")
        self.usuario = self.crear_usuario("consultor")
        self.personal = self.crear_usuario("catalogador", is_staff=True)

    def test_todos_consultan_el_catalogo(self):
        self.autenticar(self.usuario)
        respuesta = self.client.get(reverse("breed-list"))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.json()["count"], 1)

    def test_solo_el_personal_escribe_el_catalogo(self):
        self.autenticar(self.usuario)
        self.assertEqual(
            self.client.post(reverse("breed-list"), {"nombre": "Jersey"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.autenticar(self.personal)
        self.assertEqual(
            self.client.post(reverse("breed-list"), {"nombre": "Jersey"}, format="json").status_code,
            status.HTTP_201_CREATED,
        )

    def test_rechaza_razas_repetidas(self):
        self.autenticar(self.personal)
        respuesta = self.client.post(reverse("breed-list"), {"nombre": "Holstein"}, format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nombre", respuesta.json())
