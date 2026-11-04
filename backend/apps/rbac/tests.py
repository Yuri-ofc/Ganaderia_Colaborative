from django.core.management import call_command
from django.urls import reverse
from rest_framework import status

from apps.common.testing import PruebaApi
from apps.rbac.models import Recurso, Rol, RolHasRecurso, UsuarioHasRol


class PruebasRbac(PruebaApi):
    def setUp(self):
        super().setUp()
        self.admin = self.crear_usuario("administrador_rbac", con_permisos_rbac=False)
        self.operario = self.crear_usuario("operario_rbac", con_permisos_rbac=False)
        self.rbac = Recurso.objects.create(nombre="RBAC")
        self.fincas = Recurso.objects.create(nombre="FINC")
        self.rol_admin = Rol.objects.create(Rol_nombre="SUPR")
        self.rol_operario = Rol.objects.create(Rol_nombre="OPER")
        RolHasRecurso.objects.create(rol=self.rol_admin, recurso=self.rbac)
        UsuarioHasRol.objects.create(usuario=self.admin, rol=self.rol_admin)

    def test_asigna_varios_roles_a_usuario(self):
        self.autenticar(self.admin)
        respuesta = self.client.put(
            reverse("rbac-user-roles", kwargs={"usuario_id": self.operario.pk}),
            {"roles_ids": [self.rol_admin.pk, self.rol_operario.pk]},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(UsuarioHasRol.objects.filter(usuario=self.operario).values_list("rol__Rol_nombre", flat=True)),
            {"SUPR", "OPER"},
        )

    def test_login_carga_roles_y_recursos_efectivos(self):
        self.admin.email = "super@example.com"
        self.admin.save(update_fields=("email",))
        respuesta = self.client.post(
            reverse("token"), {"email": "super@example.com", "password": "Clave.Prueba.2026"}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.json()["usuario"]["roles"], ["SUPR"])
        self.assertEqual(respuesta.json()["usuario"]["recursos"], ["RBAC"])

    def test_verifica_permiso_por_recurso(self):
        UsuarioHasRol.objects.create(usuario=self.operario, rol=self.rol_operario)
        RolHasRecurso.objects.create(rol=self.rol_operario, recurso=self.fincas)
        self.autenticar(self.operario)
        respuesta = self.client.get(reverse("farm-list"))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_deniega_acceso_sin_recurso(self):
        UsuarioHasRol.objects.create(usuario=self.operario, rol=self.rol_operario)
        self.autenticar(self.operario)
        respuesta = self.client.get(reverse("backup-list"))
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)


class PruebasPoliticaEfectivaRbac(PruebaApi):
    """Cobertura de los roles reales, sin el rol TEST de la base de pruebas."""

    def setUp(self):
        super().setUp()
        call_command("seed_rbac", verbosity=0)
        self.propietaria = self.crear_usuario("duena_real", con_permisos_rbac=False)
        self.administrador = self.crear_usuario("admin_real", con_permisos_rbac=False)
        self.operario = self.crear_usuario("operario_real", con_permisos_rbac=False)
        self.superadmin = self.crear_usuario("super_real", con_permisos_rbac=False)
        self.auditor_rbac = self.crear_usuario("auditor_rbac", con_permisos_rbac=False)
        from apps.farms.models import Membresia

        self.finca = self.crear_finca(self.propietaria, "Finca auditada")
        self.agregar_miembro(self.finca, self.administrador, Membresia.Rol.ADMINISTRADOR)
        self.agregar_miembro(self.finca, self.operario, Membresia.Rol.OPERARIO)

    def test_operario_solo_recibe_los_modulos_operativos(self):
        self.autenticar(self.operario)
        self.assertEqual(self.client.get(reverse("farm-list")).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("lot-list")).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("breed-list")).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("invitation-list")).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(reverse("backup-list")).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(reverse("module-exports")).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(reverse("module-vision")).status_code, status.HTTP_403_FORBIDDEN)

    def test_operario_no_puede_modificar_una_finca_ni_bovino_existente(self):
        from apps.cattle.models import Bovino, Potrero, Raza

        raza = Raza.objects.create(nombre="Criollo")
        potrero = Potrero.objects.create(finca=self.finca, nombre="Norte")
        bovino = Bovino.objects.create(
            finca=self.finca, potrero=potrero, raza=raza, arete="OP-01", creado_por=self.propietaria,
        )
        self.autenticar(self.operario)
        finca = self.client.patch(reverse("farm-detail", kwargs={"pk": self.finca.pk}), {"nombre": "Alterada"})
        bovino_respuesta = self.client.patch(
            reverse("cattle-detail", kwargs={"pk": bovino.pk}), {"arete": "OP-02"}
        )
        self.assertEqual(finca.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(bovino_respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.finca.refresh_from_db()
        bovino.refresh_from_db()
        self.assertEqual(self.finca.nombre, "Finca auditada")
        self.assertEqual(bovino.arete, "OP-01")

    def test_propietario_no_recibe_modulo_pendiente_de_vision(self):
        self.autenticar(self.propietaria)
        self.assertEqual(self.client.get(reverse("module-vision")).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(reverse("module-exports")).status_code, status.HTTP_200_OK)

    def test_asignar_supr_actualiza_dashboard_y_recursos(self):
        # Se ejerce el mismo endpoint que usa el panel; la segunda petición
        # comprueba que la sesión de la cuenta objetivo ve el cambio efectivo.
        rol_supr = Rol.objects.get(Rol_nombre="SUPR")
        UsuarioHasRol.objects.create(usuario=self.auditor_rbac, rol=rol_supr)
        self.autenticar(self.auditor_rbac)
        asignacion = self.client.put(
            reverse("rbac-user-roles", kwargs={"usuario_id": self.superadmin.pk}),
            {"roles_ids": [rol_supr.pk]}, format="json",
        )
        self.assertEqual(asignacion.status_code, status.HTTP_200_OK)
        self.autenticar(self.superadmin)
        perfil = self.client.get(reverse("me"))
        self.assertEqual(perfil.status_code, status.HTTP_200_OK)
        self.assertIn("SUPR", perfil.json()["roles"])
        self.assertIn("RBAC", perfil.json()["recursos"])
        fincas = self.client.get(reverse("farm-list"))
        self.assertEqual(fincas.status_code, status.HTTP_200_OK)
        self.assertEqual(fincas.json()["count"], 1)
        self.assertEqual(fincas.json()["results"][0]["mi_rol"], "superadmin")
