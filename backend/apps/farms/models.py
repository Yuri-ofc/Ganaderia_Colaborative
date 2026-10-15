import uuid

from django.conf import settings
from django.db import models

from apps.common.models import ModeloBaseUuid


class Finca(ModeloBaseUuid):
    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="fincas_propias"
    )
    nombre = models.CharField(max_length=120)
    ubicacion = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.nombre


class Membresia(ModeloBaseUuid):
    class Rol(models.TextChoices):
        ADMINISTRADOR = "administrador", "Administrador"
        OPERARIO = "operario", "Operario"

    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, related_name="membresias")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membresias"
    )
    rol = models.CharField(max_length=20, choices=Rol.choices)
    invitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="membresias_invitadas"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("finca", "usuario"),
                condition=models.Q(eliminado_en__isnull=True),
                name="membresia_activa_unica_por_finca",
            ),
        ]


class Invitacion(ModeloBaseUuid):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        ACEPTADA = "aceptada", "Aceptada"
        CANCELADA = "cancelada", "Cancelada"
        EXPIRADA = "expirada", "Expirada"

    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, related_name="invitaciones")
    telefono = models.CharField(max_length=20)
    rol = models.CharField(max_length=20, choices=Membresia.Rol.choices)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    expira_en = models.DateTimeField()
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="invitaciones_creadas"
    )
    aceptado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="invitaciones_aceptadas",
    )
    aceptado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("finca", "telefono"),
                condition=models.Q(estado="pendiente", eliminado_en__isnull=True),
                name="invitacion_pendiente_unica_por_finca",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(estado="aceptada", aceptado_por__isnull=False, aceptado_en__isnull=False)
                    | (~models.Q(estado="aceptada") & models.Q(aceptado_por__isnull=True, aceptado_en__isnull=True))
                ),
                name="invitacion_aceptacion_consistente",
            ),
        ]
        indexes = [models.Index(fields=("estado", "expira_en"), name="invitacion_estado_expira_idx")]
