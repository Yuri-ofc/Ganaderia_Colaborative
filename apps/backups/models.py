from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel
from apps.farms.models import Farm


class Backup(UUIDTimeStampedModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="backups")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="backups")
    storage_url = models.URLField()
    checksum = models.CharField(max_length=128)
    size_bytes = models.PositiveBigIntegerField()
    version = models.CharField(max_length=50)
    encrypted = models.BooleanField(default=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(size_bytes__gt=0), name="backup_nonempty_size")]
        indexes = [models.Index(fields=("farm", "created_at"), name="backup_farm_created_idx")]
