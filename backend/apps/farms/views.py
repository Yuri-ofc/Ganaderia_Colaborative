from uuid import UUID

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.common.serializers import fincas_accesibles, fincas_administradas
from apps.common.views import MixinBorradoLogico, parametro_uuid

from .models import Finca, Invitacion, Membresia
from .serializers import SerializerFinca, SerializerInvitacion, SerializerMembresia

ETIQUETA_ROL = {
    Membresia.Rol.ADMINISTRADOR: "administrador",
    Membresia.Rol.OPERARIO: "operario",
}


def enviar_correo_invitacion(invitacion):
    """Envía al correo del invitado el enlace y el código para unirse a la finca.

    Si el backend de correo no está configurado (sin usuario SMTP) no se
    intenta el envío, para no romper el flujo en entornos de desarrollo.
    """
    if not settings.EMAIL_HOST_USER:
        return
    enlace = f"{settings.FRONTEND_URL}/invitaciones?token={invitacion.token}"
    rol = ETIQUETA_ROL.get(invitacion.rol, invitacion.rol)
    asunto = f"Invitación a la finca {invitacion.finca.nombre}"
    cuerpo = (
        f"Te invitaron como {rol} a la finca \"{invitacion.finca.nombre}\" "
        "en Ganadería de Precisión.\n\n"
        f"Para aceptar, abre este enlace e inicia sesión (o regístrate si aún no tienes cuenta):\n"
        f"{enlace}\n\n"
        f"Si el enlace no funciona, usa el código manualmente: {invitacion.token}\n\n"
        f"Esta invitación vence el {invitacion.expira_en:%d/%m/%Y %H:%M}."
    )
    send_mail(
        asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [invitacion.email], fail_silently=True,
    )


class VistaFincas(MixinBorradoLogico, viewsets.ModelViewSet):
    serializer_class = SerializerFinca
    recurso_requerido = "FINC"

    def get_queryset(self):
        return fincas_accesibles(self.request.user).select_related("propietario").order_by("nombre", "id")

    def perform_destroy(self, instancia):
        if instancia.propietario_id != self.request.user.pk:
            raise PermissionDenied("Solo el propietario puede eliminar la finca.")
        super().perform_destroy(instancia)


class VistaMembresias(MixinBorradoLogico, viewsets.ModelViewSet):
    serializer_class = SerializerMembresia
    recurso_requerido = "MIEM"

    def get_queryset(self):
        consulta = Membresia.objects.filter(
            finca__in=fincas_administradas(self.request.user), eliminado_en__isnull=True
        ).select_related("finca", "usuario", "invitado_por")
        finca_id = parametro_uuid(self.request, "finca")
        if finca_id:
            consulta = consulta.filter(finca_id=finca_id)
        return consulta.order_by("-creado_en", "-id")

    def perform_destroy(self, instancia):
        if instancia.rol == Membresia.Rol.ADMINISTRADOR and instancia.finca.propietario_id != self.request.user.pk:
            raise PermissionDenied("Solo el propietario puede retirar administradores.")
        super().perform_destroy(instancia)


class VistaInvitaciones(MixinBorradoLogico, viewsets.ModelViewSet):
    serializer_class = SerializerInvitacion
    recurso_requerido = "INVT"

    def get_queryset(self):
        consulta = Invitacion.objects.filter(
            finca__in=fincas_administradas(self.request.user), eliminado_en__isnull=True
        ).select_related("finca", "creado_por", "aceptado_por")
        finca_id = parametro_uuid(self.request, "finca")
        if finca_id:
            consulta = consulta.filter(finca_id=finca_id)
        return consulta.order_by("-creado_en", "-id")

    def perform_create(self, serializer):
        invitacion = serializer.save()
        enviar_correo_invitacion(invitacion)

    def perform_destroy(self, instancia):
        if instancia.estado != Invitacion.Estado.PENDIENTE:
            raise ValidationError("Solo se pueden cancelar invitaciones pendientes.")
        if instancia.rol == Membresia.Rol.ADMINISTRADOR and instancia.finca.propietario_id != self.request.user.pk:
            raise PermissionDenied("Solo el propietario puede cancelar invitaciones de administrador.")
        instancia.estado = Invitacion.Estado.CANCELADA
        instancia.eliminado_en = timezone.now()
        instancia.save(update_fields=("estado", "eliminado_en", "actualizado_en"))

    @action(detail=False, methods=("post",), url_path="accept", url_name="accept")
    def aceptar(self, request):
        token = request.data.get("token")
        if not token:
            raise ValidationError({"token": "Este campo es obligatorio."})
        try:
            token_id = UUID(str(token))
        except (TypeError, ValueError, AttributeError):
            raise ValidationError({"token": "Debe ser un UUID válido."})
        with transaction.atomic():
            invitacion = Invitacion.objects.select_for_update().filter(
                token=token_id, estado=Invitacion.Estado.PENDIENTE, eliminado_en__isnull=True,
                finca__eliminado_en__isnull=True,
            ).select_related("finca").first()
            if invitacion is None:
                raise ValidationError({"token": "Invitación inválida o ya utilizada."})
            if invitacion.expira_en <= timezone.now():
                invitacion.estado = Invitacion.Estado.EXPIRADA
                invitacion.save(update_fields=("estado", "actualizado_en"))
                return Response({"token": ["La invitación ha vencido."]}, status=status.HTTP_400_BAD_REQUEST)
            if not request.user.telefono or request.user.telefono != invitacion.telefono:
                raise PermissionDenied("La invitación corresponde a otro número de teléfono.")
            if invitacion.finca.propietario_id == request.user.pk:
                raise ValidationError({"token": "El propietario ya pertenece a la finca."})
            membresia, creada = Membresia.objects.get_or_create(
                finca=invitacion.finca,
                usuario=request.user,
                eliminado_en__isnull=True,
                defaults={"rol": invitacion.rol, "invitado_por": invitacion.creado_por},
            )
            invitacion.estado = Invitacion.Estado.ACEPTADA
            invitacion.aceptado_por = request.user
            invitacion.aceptado_en = timezone.now()
            invitacion.save(update_fields=("estado", "aceptado_por", "aceptado_en", "actualizado_en"))
        return Response(
            {"membresia_id": str(membresia.pk), "finca_id": str(invitacion.finca_id), "creada": creada},
            status=status.HTTP_201_CREATED if creada else status.HTTP_200_OK,
        )
