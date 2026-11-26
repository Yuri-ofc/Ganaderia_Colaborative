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

    def test_listado_de_usuarios_oculta_a_los_superusuarios(self):
        superusuario = self.crear_usuario("superusuario_django", con_permisos_rbac=False, is_superuser=True)
        self.autenticar(self.admin)
        respuesta = self.client.get(reverse("rbac-users"))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        nombres = {u["username"] for u in respuesta.json()}
        self.assertIn("operario_rbac", nombres)
        self.assertNotIn(superusuario.username, nombres)
        # Tampoco aparece al buscarlo por nombre.
        buscado = self.client.get(reverse("rbac-users"), {"q": "superusuario"})
        self.assertEqual(buscado.json(), [])

    def test_no_se_pueden_consultar_ni_cambiar_roles_de_un_superusuario(self):
        superusuario = self.crear_usuario("superusuario_django", con_permisos_rbac=False, is_superuser=True)
        self.autenticar(self.admin)
        url = reverse("rbac-user-roles", kwargs={"usuario_id": superusuario.pk})
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        cambio = self.client.put(url, {"roles_ids": [self.rol_operario.pk]}, format="json")
        self.assertEqual(cambio.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(UsuarioHasRol.objects.filter(usuario=superusuario).exists())

    def test_crea_usuario_desde_control_de_acceso_y_puede_iniciar_sesion(self):
        self.autenticar(self.admin)
        datos = {"username": "nuevo_rbac", "email": "Nuevo@Example.com", "telefono": "3001112233", "password": "Clave.Nueva.2026"}
        respuesta = self.client.post(reverse("rbac-users"), datos, format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", respuesta.json())
        # Aparece en el listado del panel.
        nombres = {u["username"] for u in self.client.get(reverse("rbac-users")).json()}
        self.assertIn("nuevo_rbac", nombres)
        # Y entra por el login normal, con correo, sin ningún paso extra.
        self.desautenticar()
        login = self.client.post(
            reverse("token"), {"email": "nuevo@example.com", "password": "Clave.Nueva.2026"}, format="json"
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertEqual(login.json()["usuario"]["username"], "nuevo_rbac")

    def test_crear_usuario_valida_duplicados_y_correo_obligatorio(self):
        self.autenticar(self.admin)
        base = {"username": "otro_rbac", "email": "otro@example.com", "password": "Clave.Nueva.2026"}
        self.assertEqual(self.client.post(reverse("rbac-users"), base, format="json").status_code, 201)
        repetido = self.client.post(reverse("rbac-users"), {**base, "username": "otro_rbac2"}, format="json")
        self.assertEqual(repetido.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", repetido.json())
        sin_correo = self.client.post(reverse("rbac-users"), {**base, "username": "x_rbac", "email": ""}, format="json")
        self.assertEqual(sin_correo.status_code, status.HTTP_400_BAD_REQUEST)
        debil = self.client.post(reverse("rbac-users"), {**base, "username": "y_rbac", "email": "y@example.com", "password": "123"}, format="json")
        self.assertEqual(debil.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crear_usuario_exige_el_recurso_rbac(self):
        self.autenticar(self.operario)
        datos = {"username": "intruso", "email": "i@example.com", "password": "Clave.Nueva.2026"}
        self.assertEqual(self.client.post(reverse("rbac-users"), datos, format="json").status_code, status.HTTP_403_FORBIDDEN)

    def test_etiqueta_de_recurso_se_edita_hasta_60_caracteres_y_llega_al_menu(self):
        self.autenticar(self.admin)
        url = reverse("rbac-resource-detail", kwargs={"pk": self.fincas.pk})
        larga = "Gestión de fincas y potreros de la hacienda"
        respuesta = self.client.patch(url, {"etiqueta": f"  {larga}  "}, format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.json()["etiqueta"], larga)
        self.assertEqual(respuesta.json()["nombre"], "FINC")  # el código no cambia
        self.assertEqual(self.client.patch(url, {"etiqueta": "x" * 61}, format="json").status_code, 400)
        # Cualquier sesión activa lee las etiquetas para pintar el menú.
        self.autenticar(self.operario)
        etiquetas = self.client.get(reverse("rbac-labels")).json()["etiquetas"]
        self.assertEqual(etiquetas["FINC"], larga)
        self.assertEqual(etiquetas["RBAC"], "RBAC")  # sin etiqueta: se muestra el código

    def test_crea_opcion_nueva_del_dashboard_con_codigo_automatico(self):
        self.autenticar(self.admin)
        url = reverse("rbac-menu-options")
        creada = self.client.post(url, {"etiqueta": "  Reportes   de campo "}, format="json")
        self.assertEqual(creada.status_code, status.HTTP_201_CREATED)
        self.assertEqual(creada.json()["etiqueta"], "Reportes de campo")
        self.assertEqual(creada.json()["nombre"], "REPO")
        self.assertTrue(creada.json()["opcion_menu"])
        # Mismo inicio de nombre: el código se desambigua.
        segunda = self.client.post(url, {"etiqueta": "Reporte mensual"}, format="json")
        self.assertEqual(segunda.json()["nombre"], "REP1")
        # Etiqueta repetida o vacía se rechaza.
        self.assertEqual(self.client.post(url, {"etiqueta": "reportes de campo"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(url, {"etiqueta": "  "}, format="json").status_code, 400)
        # Cualquier sesión recibe las opciones nuevas para pintar el menú.
        self.autenticar(self.operario)
        opciones = self.client.get(reverse("rbac-labels")).json()["opciones"]
        self.assertEqual({o["nombre"] for o in opciones}, {"REPO", "REP1"})

    def test_solo_rbac_crea_opciones_y_seed_no_las_elimina(self):
        self.autenticar(self.operario)
        self.assertEqual(self.client.post(reverse("rbac-menu-options"), {"etiqueta": "Algo"}, format="json").status_code, 403)
        Recurso.objects.create(nombre="NUEV", etiqueta="Nueva", opcion_menu=True)
        call_command("seed_rbac", verbosity=0)
        self.assertTrue(Recurso.objects.filter(nombre="NUEV").exists())

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
        self.assertEqual(self.client.get(reverse("export-list")).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(reverse("vision-capture-list")).status_code, status.HTTP_403_FORBIDDEN)

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

    def test_propietario_exporta_pero_no_entra_a_vision(self):
        self.autenticar(self.propietaria)
        self.assertEqual(
            self.client.get(reverse("vision-capture-list")).status_code, status.HTTP_403_FORBIDDEN
        )
        exportacion = self.client.get(
            reverse("export-list"), {"finca": str(self.finca.pk), "incluir": "bovinos"}
        )
        self.assertEqual(exportacion.status_code, status.HTTP_200_OK)
        self.assertIn("attachment", exportacion["Content-Disposition"])

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


class PruebasProteccionCatalogoRbac(PruebaApi):
    """El catálogo base no se puede romper desde el propio panel (DT-04)."""

    def setUp(self):
        super().setUp()
        call_command("seed_rbac", verbosity=0)
        self.auditor = self.crear_usuario("auditor_catalogo", con_permisos_rbac=False)
        UsuarioHasRol.objects.create(usuario=self.auditor, rol=Rol.objects.get(Rol_nombre="SUPR"))
        self.autenticar(self.auditor)

    def test_no_se_elimina_un_rol_del_sistema(self):
        rol = Rol.objects.get(Rol_nombre="SUPR")
        respuesta = self.client.delete(reverse("rbac-role-detail", kwargs={"pk": rol.pk}))
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Rol.objects.filter(Rol_nombre="SUPR").exists())

    def test_no_se_renombra_un_rol_del_sistema(self):
        rol = Rol.objects.get(Rol_nombre="PROP")
        respuesta = self.client.patch(
            reverse("rbac-role-detail", kwargs={"pk": rol.pk}), {"Rol_nombre": "XXXX"}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        rol.refresh_from_db()
        self.assertEqual(rol.Rol_nombre, "PROP")

    def test_los_recursos_de_un_rol_operativo_siguen_siendo_administrables(self):
        rol = Rol.objects.get(Rol_nombre="ADMI")
        recurso = Recurso.objects.get(nombre="BOVI")
        respuesta = self.client.patch(
            reverse("rbac-role-detail", kwargs={"pk": rol.pk}),
            {"recursos_ids": [recurso.idrecurso]}, format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(list(rol.recursos.values_list("nombre", flat=True)), ["BOVI"])

    def test_el_superadministrador_conserva_todos_sus_recursos(self):
        rol = Rol.objects.get(Rol_nombre="SUPR")
        total = rol.recursos.count()
        respuesta = self.client.patch(
            reverse("rbac-role-detail", kwargs={"pk": rol.pk}),
            {"recursos_ids": [Recurso.objects.get(nombre="BOVI").idrecurso]}, format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rol.recursos.count(), total)

    def test_no_se_elimina_ni_renombra_un_recurso_del_sistema_pero_si_su_etiqueta(self):
        recurso = Recurso.objects.get(nombre="RBAC")
        url = reverse("rbac-resource-detail", kwargs={"pk": recurso.pk})
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.client.patch(url, {"nombre": "ZZZZ"}, format="json").status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        etiquetado = self.client.patch(url, {"etiqueta": "Permisos"}, format="json")
        self.assertEqual(etiquetado.status_code, status.HTTP_200_OK)
        recurso.refresh_from_db()
        self.assertEqual(recurso.nombre, "RBAC")
        self.assertEqual(recurso.etiqueta, "Permisos")

    def test_un_rol_propio_del_administrador_si_se_elimina(self):
        rol = Rol.objects.create(Rol_nombre="AUDI")
        respuesta = self.client.delete(reverse("rbac-role-detail", kwargs={"pk": rol.pk}))
        self.assertEqual(respuesta.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Rol.objects.filter(Rol_nombre="AUDI").exists())

    def test_nadie_edita_sus_propios_accesos(self):
        respuesta = self.client.put(
            reverse("rbac-user-roles", kwargs={"usuario_id": self.auditor.pk}),
            {"roles_ids": []}, format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(UsuarioHasRol.objects.filter(usuario=self.auditor).exists())
