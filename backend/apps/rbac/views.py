import re
import unicodedata

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .constantes import RECURSOS_SISTEMA, ROLES_SISTEMA
from .models import Recurso, Rol, UsuarioHasRol
from .serializers import (
    SerializerNuevoUsuario,
    SerializerRecurso,
    SerializerRol,
    SerializerUsuarioRbac,
    roles_y_recursos_usuario,
)

Usuario = get_user_model()


def usuarios_administrables():
    """Cuentas cuyos roles se pueden consultar y cambiar desde el panel RBAC.

    Los superusuarios de Django quedan fuera: tienen acceso total por
    definición (ver `es_superadministrador`) y no se les puede modificar.
    """
    return Usuario.objects.filter(is_active=True, is_superuser=False, eliminado_en__isnull=True)


class VistaRoles(viewsets.ModelViewSet):
    queryset = Rol.objects.prefetch_related("recursos").all()
    serializer_class = SerializerRol
    recurso_requerido = "RBAC"

    def perform_update(self, serializer):
        """Los cuatro roles del catálogo conservan su código y SUPR sus recursos.

        Repartir recursos entre PROP, ADMI y OPER es administración normal; en
        cambio renombrarlos deja huérfanos los ``recurso_requerido`` de las
        vistas, y recortarle recursos a SUPR deja el sistema sin nadie que
        pueda repararlo.
        """
        rol = serializer.instance
        if rol.Rol_nombre in ROLES_SISTEMA:
            nombre_nuevo = serializer.validated_data.get("Rol_nombre", rol.Rol_nombre)
            if nombre_nuevo != rol.Rol_nombre:
                raise ValidationError(
                    {"Rol_nombre": f"El rol {rol.Rol_nombre} es del sistema y no se puede renombrar."}
                )
            if rol.Rol_nombre == "SUPR" and "recursos" in serializer.validated_data:
                raise ValidationError(
                    {"recursos_ids": "El superadministrador conserva todos los accesos."}
                )
        serializer.save()

    def perform_destroy(self, instancia):
        if instancia.Rol_nombre in ROLES_SISTEMA:
            raise ValidationError(
                {"Rol_nombre": f"El rol {instancia.Rol_nombre} es del sistema y no se puede eliminar."}
            )
        instancia.delete()


class VistaRecursos(viewsets.ModelViewSet):
    queryset = Recurso.objects.all()
    serializer_class = SerializerRecurso
    recurso_requerido = "RBAC"

    def perform_update(self, serializer):
        """La etiqueta visible se cambia siempre; el código base nunca.

        El ``nombre`` es el código que valida el servidor en cada vista, así
        que cambiarlo apagaría el módulo correspondiente para todos.
        """
        recurso = serializer.instance
        if recurso.nombre in RECURSOS_SISTEMA:
            nombre_nuevo = serializer.validated_data.get("nombre", recurso.nombre)
            if nombre_nuevo != recurso.nombre:
                raise ValidationError(
                    {"nombre": f"El código {recurso.nombre} es del sistema; cambia solo su etiqueta."}
                )
        serializer.save()

    def perform_destroy(self, instancia):
        if instancia.nombre in RECURSOS_SISTEMA:
            raise ValidationError(
                {"nombre": f"El acceso {instancia.nombre} es del sistema y no se puede eliminar."}
            )
        instancia.delete()


class VistaUsuariosRbac(APIView):
    recurso_requerido = "RBAC"

    def get(self, solicitud):
        termino = solicitud.query_params.get("q", "").strip()
        consulta = usuarios_administrables().order_by("username")
        if termino:
            consulta = consulta.filter(username__icontains=termino)
        usuarios = list(consulta[:50])
        for usuario in usuarios:
            roles, _ = roles_y_recursos_usuario(usuario)
            usuario.roles_rbac = roles
        return Response(SerializerUsuarioRbac(usuarios, many=True).data)

    def post(self, solicitud):
        serializer = SerializerNuevoUsuario(data=solicitud.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        usuario.roles_rbac = []
        return Response(SerializerUsuarioRbac(usuario).data, status=status.HTTP_201_CREATED)


class VistaEtiquetasRecursos(APIView):
    """Etiquetas de menú por código de recurso, para cualquier sesión activa.

    No declara ``recurso_requerido``: solo expone textos de interfaz, nunca
    permisos. Los accesos reales siguen viniendo del perfil y del servidor.
    """

    def get(self, solicitud):
        recursos = list(Recurso.objects.all())
        return Response({
            "etiquetas": {recurso.nombre: recurso.etiqueta_visible for recurso in recursos},
            "opciones": [
                {"nombre": recurso.nombre, "etiqueta": recurso.etiqueta_visible}
                for recurso in recursos
                if recurso.opcion_menu
            ],
        })


def _codigo_para(etiqueta):
    """Código de cuatro caracteres libre a partir del texto de la etiqueta."""
    texto = unicodedata.normalize("NFKD", etiqueta).encode("ascii", "ignore").decode().upper()
    base = (re.sub(r"[^A-Z]", "", texto) + "XXXX")[:4]
    if not Recurso.objects.filter(nombre=base).exists():
        return base
    for numero in range(1, 1000):
        sufijo = str(numero)
        candidato = base[: 4 - len(sufijo)] + sufijo
        if not Recurso.objects.filter(nombre=candidato).exists():
            return candidato
    raise ValidationError({"etiqueta": "No hay códigos libres para esta etiqueta."})


class VistaOpcionesMenu(APIView):
    """Crea una opción nueva del dashboard (recurso + entrada de menú)."""

    recurso_requerido = "RBAC"

    def post(self, solicitud):
        # Parcial: aquí solo se valida la etiqueta; el código lo genera el servidor.
        datos = SerializerRecurso(data={"etiqueta": solicitud.data.get("etiqueta", "")}, partial=True)
        datos.is_valid(raise_exception=True)
        etiqueta = datos.validated_data["etiqueta"]
        if not etiqueta:
            raise ValidationError({"etiqueta": "Escribe el nombre de la opción."})
        recurso = Recurso.objects.create(nombre=_codigo_para(etiqueta), etiqueta=etiqueta, opcion_menu=True)
        return Response(SerializerRecurso(recurso).data, status=status.HTTP_201_CREATED)


class VistaRolesUsuario(APIView):
    recurso_requerido = "RBAC"

    def _usuario(self, usuario_id):
        try:
            return usuarios_administrables().get(pk=usuario_id)
        except Usuario.DoesNotExist as error:
            raise NotFound("Usuario no encontrado.") from error

    def get(self, solicitud, usuario_id):
        usuario = self._usuario(usuario_id)
        roles, recursos = roles_y_recursos_usuario(usuario)
        usuario.roles_rbac = roles
        datos = SerializerUsuarioRbac(usuario).data
        datos["recursos"] = recursos
        return Response(datos)

    def put(self, solicitud, usuario_id):
        usuario = self._usuario(usuario_id)
        # Nadie edita sus propios accesos: evita tanto quitarse SUPR y quedar
        # fuera del panel como ampliarse permisos sin que lo revise un tercero.
        if usuario.pk == solicitud.user.pk:
            return Response(
                {"roles_ids": "No puede modificar sus propios accesos; pídalo a otro superadministrador."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        roles_ids = solicitud.data.get("roles_ids")
        if not isinstance(roles_ids, list):
            return Response({"roles_ids": "Debe enviar una lista de identificadores."}, status=status.HTTP_400_BAD_REQUEST)
        roles = list(Rol.objects.filter(pk__in=roles_ids))
        if len(roles) != len(set(roles_ids)):
            return Response({"roles_ids": "Uno o más roles no existen."}, status=status.HTTP_400_BAD_REQUEST)
        # El borrado y el alta van juntos: si falla el alta, el usuario no se
        # queda sin los roles que ya tenía.
        with transaction.atomic():
            UsuarioHasRol.objects.filter(usuario=usuario).exclude(rol__in=roles).delete()
            existentes = set(UsuarioHasRol.objects.filter(usuario=usuario).values_list("rol_id", flat=True))
            UsuarioHasRol.objects.bulk_create(
                [UsuarioHasRol(usuario=usuario, rol=rol) for rol in roles if rol.pk not in existentes]
            )
        roles, recursos = roles_y_recursos_usuario(usuario)
        usuario.roles_rbac = roles
        datos = SerializerUsuarioRbac(usuario).data
        datos["recursos"] = recursos
        return Response(datos)
