import re
import unicodedata

from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

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


class VistaRecursos(viewsets.ModelViewSet):
    queryset = Recurso.objects.all()
    serializer_class = SerializerRecurso
    recurso_requerido = "RBAC"


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
        roles_ids = solicitud.data.get("roles_ids")
        if not isinstance(roles_ids, list):
            return Response({"roles_ids": "Debe enviar una lista de identificadores."}, status=status.HTTP_400_BAD_REQUEST)
        roles = list(Rol.objects.filter(pk__in=roles_ids))
        if len(roles) != len(set(roles_ids)):
            return Response({"roles_ids": "Uno o más roles no existen."}, status=status.HTTP_400_BAD_REQUEST)
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
