from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Recurso, Rol, UsuarioHasRol
from .serializers import SerializerRecurso, SerializerRol, SerializerUsuarioRbac, roles_y_recursos_usuario

Usuario = get_user_model()


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
        consulta = Usuario.objects.filter(is_active=True, eliminado_en__isnull=True).order_by("username")
        if termino:
            consulta = consulta.filter(username__icontains=termino)
        usuarios = list(consulta[:50])
        for usuario in usuarios:
            roles, _ = roles_y_recursos_usuario(usuario)
            usuario.roles_rbac = roles
        return Response(SerializerUsuarioRbac(usuarios, many=True).data)


class VistaRolesUsuario(APIView):
    recurso_requerido = "RBAC"

    def _usuario(self, usuario_id):
        try:
            return Usuario.objects.get(pk=usuario_id, is_active=True, eliminado_en__isnull=True)
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
