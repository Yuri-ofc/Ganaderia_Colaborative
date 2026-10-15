from django.conf import settings
from django.db import models

from apps.common.models import ModeloBaseUuid
from apps.farms.models import Finca
from apps.measurements.models import Dispositivo


class CambioSincronizacion(ModeloBaseUuid):
    class Accion(models.TextChoices):
        CREAR = "crear", "Crear"
        ACTUALIZAR = "actualizar", "Actualizar"
        ELIMINAR = "eliminar", "Eliminar"

    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, related_name="cambios_sincronizacion")
    dispositivo = models.ForeignKey(
        Dispositivo, on_delete=models.PROTECT, related_name="cambios_sincronizacion"
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cambios_sincronizacion"
    )
    id_cambio_cliente = models.UUIDField()
    recurso = models.CharField(max_length=100)
    id_objeto = models.UUIDField()
    accion = models.CharField(max_length=10, choices=Accion.choices)
    contenido = models.JSONField(default=dict)
    sincronizado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("dispositivo", "id_cambio_cliente"),
                name="cambio_cliente_unico_por_dispositivo",
            ),
            models.CheckConstraint(
                condition=models.Q(sincronizado_en__isnull=True)
                | models.Q(sincronizado_en__gte=models.F("creado_en")),
                name="sincronizacion_posterior_a_creacion",
            ),
        ]
        indexes = [models.Index(fields=("finca", "creado_en"), name="cambio_finca_creado_idx")]
