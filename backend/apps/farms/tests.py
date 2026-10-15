from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.common.testing import PruebaApi

from .models import Invitacion, Membresia


class PruebasAislamientoFincas(PruebaApi):
    def setUp(self):
        super().setUp()
        self.propietaria = self.crear_usuario("propietaria")
        self.operario = self.crear_usuario("operario")
        self.ajena = self.crear_usuario("ajena")
        self.finca = self.crear_finca(self.propietaria, "Finca Propia")
        self.finca_ajena = self.crear_finca(self.ajena, "Finca Ajena")
        self.agregar_miembro(self.finca, self.operario, Membresia.Rol.OPERARIO)

    def test_la_lista_solo_muestra_las_fincas_accesibles(self):
        self.autenticar(self.propietaria)
        cuerpo = self.client.get(reverse("farm-list")).json()
        self.assertEqual([f["id"] for f in cuerpo["results"]], [str(self.finca.pk)])

        self.autenticar(self.operario)
        cuerpo = self.client.get(reverse("farm-list")).json()
        self.assertEqual([f["id"] for f in cuerpo["results"]], [str(self.finca.pk)])

        self.autenticar(self.ajena)
        cuerpo = self.client.get(reverse("farm-list")).json()
        self.assertEqual([f["id"] for f in cuerpo["results"]], [str(self.finca_ajena.pk)])

    def test_no_se_puede_consultar_una_finca_ajena(self):
        self.autenticar(self.propietaria)
        respuesta = self.client.get(reverse("farm-detail", args=[self.finca_ajena.pk]))
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_no_se_puede_modificar_una_finca_ajena(self):
        self.autenticar(self.propietaria)
        respuesta = self.client.patch(
            reverse("farm-detail", args=[self.finca_ajena.pk]), {"nombre": "Secuestrada"}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)
        self.finca_ajena.refresh_from_db()
        self.assertEqual(self.finca_ajena.nombre, "Finca Ajena")

    def test_los_miembros_no_renombran_ni_eliminan_la_finca(self):
        self.autenticar(self.operario)
        self.assertEqual(
            self.client.patch(
                reverse("farm-detail", args=[self.finca.pk]), {"nombre": "Renombrada"}, format="json"
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.delete(reverse("farm-detail", args=[self.finca.pk])).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_la_creacion_asigna_al_usuario_autenticado(self):
        self.autenticar(self.operario)
        respuesta = self.client.post(
            reverse("farm-list"), {"nombre": "Finca Nueva", "propietario": str(self.ajena.pk)}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.json()["propietario"], str(self.operario.pk))

    def test_el_borrado_del_propietario_es_logico(self):
        self.autenticar(self.propietaria)
        respuesta = self.client.delete(reverse("farm-detail", args=[self.finca.pk]))
        self.assertEqual(respuesta.status_code, status.HTTP_204_NO_CONTENT)
        self.finca.refresh_from_db()
        self.assertIsNotNone(self.finca.eliminado_en)
        self.assertEqual(self.client.get(reverse("farm-list")).json()["count"], 0)


class PruebasRolesMembresia(PruebaApi):
    def setUp(self):
        super().setUp()
        self.duena = self.crear_usuario("duena")
        self.administrador = self.crear_usuario("administrador")
        self.operaria = self.crear_usuario("operaria")
        self.candidato = self.crear_usuario("candidato")
        self.finca = self.crear_finca(self.duena)
        self.agregar_miembro(self.finca, self.administrador, Membresia.Rol.ADMINISTRADOR)
        self.agregar_miembro(self.finca, self.operaria, Membresia.Rol.OPERARIO)

    def test_el_operario_no_gestiona_membresias(self):
        self.autenticar(self.operaria)
        self.assertEqual(self.client.get(reverse("membership-list")).json()["count"], 0)
        respuesta = self.client.post(
            reverse("membership-list"),
            {"finca": str(self.finca.pk), "usuario": str(self.candidato.pk), "rol": "operario"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("finca", respuesta.json())

    def test_el_administrador_agrega_operarios(self):
        self.autenticar(self.administrador)
        respuesta = self.client.post(
            reverse("membership-list"),
            {"finca": str(self.finca.pk), "usuario": str(self.candidato.pk), "rol": "operario"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.json()["invitado_por"], str(self.administrador.pk))

    def test_solo_el_propietario_asigna_administradores(self):
        self.autenticar(self.administrador)
        respuesta = self.client.post(
            reverse("membership-list"),
            {"finca": str(self.finca.pk), "usuario": str(self.candidato.pk), "rol": "administrador"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

        self.autenticar(self.duena)
        respuesta = self.client.post(
            reverse("membership-list"),
            {"finca": str(self.finca.pk), "usuario": str(self.candidato.pk), "rol": "administrador"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

    def test_un_administrador_no_retira_a_otro(self):
        membresia = Membresia.objects.get(usuario=self.administrador)
        self.autenticar(self.administrador)
        respuesta = self.client.delete(reverse("membership-detail", args=[membresia.pk]))
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_rechaza_membresias_activas_repetidas(self):
        self.autenticar(self.duena)
        respuesta = self.client.post(
            reverse("membership-list"),
            {"finca": str(self.finca.pk), "usuario": str(self.operaria.pk), "rol": "operario"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("usuario", respuesta.json())

    def test_las_membresias_de_otras_fincas_son_invisibles(self):
        otra_duena = self.crear_usuario("otra_duena")
        otra_finca = self.crear_finca(otra_duena)
        otra_membresia = self.agregar_miembro(otra_finca, self.candidato, Membresia.Rol.OPERARIO)
        self.autenticar(self.duena)
        listado = self.client.get(reverse("membership-list")).json()
        self.assertNotIn(str(otra_membresia.pk), [item["id"] for item in listado["results"]])
        self.assertEqual(
            self.client.get(reverse("membership-detail", args=[otra_membresia.pk])).status_code,
            status.HTTP_404_NOT_FOUND,
        )


class PruebasInvitaciones(PruebaApi):
    def setUp(self):
        super().setUp()
        self.anfitriona = self.crear_usuario("anfitriona", telefono="+573009990000")
        self.invitado = self.crear_usuario("invitado", telefono="+573009991111")
        self.finca = self.crear_finca(self.anfitriona)

    def crear_invitacion(self, **extra):
        valores = {
            "finca": self.finca,
            "telefono": self.invitado.telefono,
            "rol": Membresia.Rol.OPERARIO,
            "expira_en": timezone.now() + timedelta(days=3),
            "creado_por": self.anfitriona,
        }
        return Invitacion.objects.create(**{**valores, **extra})

    def test_el_propietario_crea_invitaciones_pendientes(self):
        self.autenticar(self.anfitriona)
        respuesta = self.client.post(
            reverse("invitation-list"),
            {
                "finca": str(self.finca.pk),
                "telefono": "+573009992222",
                "rol": "operario",
                "expira_en": (timezone.now() + timedelta(days=2)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.json()["estado"], Invitacion.Estado.PENDIENTE)

    def test_el_vencimiento_debe_ser_futuro(self):
        self.autenticar(self.anfitriona)
        respuesta = self.client.post(
            reverse("invitation-list"),
            {
                "finca": str(self.finca.pk),
                "telefono": "+573009993333",
                "rol": "operario",
                "expira_en": (timezone.now() - timedelta(days=1)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expira_en", respuesta.json())

    def test_aceptar_crea_la_membresia(self):
        invitacion = self.crear_invitacion()
        self.autenticar(self.invitado)
        respuesta = self.client.post(
            reverse("invitation-accept"), {"token": str(invitacion.token)}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Membresia.objects.filter(
                finca=self.finca, usuario=self.invitado, rol=Membresia.Rol.OPERARIO
            ).exists()
        )
        invitacion.refresh_from_db()
        self.assertEqual(invitacion.estado, Invitacion.Estado.ACEPTADA)
        self.assertEqual(invitacion.aceptado_por, self.invitado)
        self.assertIsNotNone(invitacion.aceptado_en)

    def test_otro_telefono_no_puede_aceptar(self):
        invitacion = self.crear_invitacion()
        intrusa = self.crear_usuario("intrusa", telefono="+573009994444")
        self.autenticar(intrusa)
        respuesta = self.client.post(
            reverse("invitation-accept"), {"token": str(invitacion.token)}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Membresia.objects.filter(usuario=intrusa).exists())

    def test_una_invitacion_vencida_se_cierra(self):
        invitacion = self.crear_invitacion(expira_en=timezone.now() - timedelta(minutes=1))
        self.autenticar(self.invitado)
        respuesta = self.client.post(
            reverse("invitation-accept"), {"token": str(invitacion.token)}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        invitacion.refresh_from_db()
        self.assertEqual(invitacion.estado, Invitacion.Estado.EXPIRADA)

    def test_las_invitaciones_de_otras_fincas_son_invisibles(self):
        otro_anfitrion = self.crear_usuario("otro_anfitrion")
        otra_finca = self.crear_finca(otro_anfitrion)
        otra_invitacion = self.crear_invitacion(finca=otra_finca, creado_por=otro_anfitrion)
        self.autenticar(self.anfitriona)
        self.assertEqual(
            self.client.get(reverse("invitation-detail", args=[otra_invitacion.pk])).status_code,
            status.HTTP_404_NOT_FOUND,
        )


class PruebasParametrosConsulta(PruebaApi):
    def test_rechaza_un_uuid_invalido(self):
        usuario = self.crear_usuario("consultora")
        self.autenticar(usuario)
        respuesta = self.client.get(reverse("membership-list"), {"finca": "no-es-uuid"})
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("finca", respuesta.json())
