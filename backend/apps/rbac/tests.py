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
        respuesta = self.client.get(reverse("farm-list"))
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
