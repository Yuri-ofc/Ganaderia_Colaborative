from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel
from apps.farms.models import Farm
from apps.measurements.models import Device


class SyncChange(UUIDTimeStampedModel):
    class Action(models.TextChoices):
        CREATE = "create", "Crear"
        UPDATE = "update", "Actualizar"
        DELETE = "delete", "Eliminar"

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="sync_changes")
    device = models.ForeignKey(Device, on_delete=models.PROTECT, related_name="sync_changes")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sync_changes")
    client_change_id = models.UUIDField()
    resource = models.CharField(max_length=100)
    object_id = models.UUIDField()
    action = models.CharField(max_length=10, choices=Action.choices)
    payload = models.JSONField(default=dict)
    synchronized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("device", "client_change_id"), name="unique_device_client_change"),
            models.CheckConstraint(
                condition=models.Q(synchronized_at__isnull=True) | models.Q(synchronized_at__gte=models.F("created_at")),
                name="sync_time_after_creation",
            ),
        ]
        indexes = [models.Index(fields=("farm", "created_at"), name="sync_farm_created_idx")]
