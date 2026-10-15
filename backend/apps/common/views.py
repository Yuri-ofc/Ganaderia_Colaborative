from uuid import UUID

from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAdminUser, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from .permissions import PermisoUsuarioActivo

__all__ = [
    "MixinBorradoLogico",
    "MixinEscrituraPersonal",
    "PermisoUsuarioActivo",
    "VistaRaizApi",
    "parametro_uuid",
]


def parametro_uuid(solicitud, nombre):
    valor = solicitud.query_params.get(nombre)
    if valor is None or valor == "":
        return None
    try:
        return UUID(valor)
    except (TypeError, ValueError, AttributeError):
        raise ValidationError({nombre: "Debe ser un UUID válido."})


class MixinBorradoLogico:
    def perform_destroy(self, instancia):
        instancia.eliminado_en = timezone.now()
        instancia.save(update_fields=("eliminado_en", "actualizado_en"))


class MixinEscrituraPersonal:
    def get_permissions(self):
        permisos = [PermisoUsuarioActivo()]
        if self.request.method not in SAFE_METHODS:
            permisos.append(IsAdminUser())
        return permisos


class VistaRaizApi(APIView):
    permission_classes = (AllowAny,)

    rutas = (
        ("register", "register"),
        ("token", "token"),
        ("logout", "logout"),
        ("farms", "farm-list"),
        ("memberships", "membership-list"),
        ("invitations", "invitation-list"),
        ("breeds", "breed-list"),
        ("lots", "lot-list"),
        ("cattle", "cattle-list"),
        ("lot-movements", "lot-movement-list"),
        ("devices", "device-list"),
        ("ai-models", "ai-model-list"),
        ("measurement-types", "measurement-type-list"),
        ("measurements", "measurement-list"),
        ("morphometric-measurements", "morphometric-measurement-list"),
        ("scale-weighings", "scale-weighing-list"),
        ("backups", "backup-list"),
        ("sync-changes", "sync-change-list"),
    )

    def get(self, solicitud):
        return Response(
            {
                "version": "v1",
                "endpoints": {
                    etiqueta: reverse(nombre, request=solicitud) for etiqueta, nombre in self.rutas
                },
            }
        )
