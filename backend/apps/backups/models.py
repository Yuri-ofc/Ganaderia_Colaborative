from django.conf import settings
from django.db import models

from apps.common.models import ModeloBaseUuid
from apps.farms.models import Finca


class Respaldo(ModeloBaseUuid):
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, related_name="respaldos")
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="respaldos"
    )
    url_almacenamiento = models.URLField()
    suma_verificacion = models.CharField(max_length=128)
    tamano_bytes = models.PositiveBigIntegerField()
    version = models.CharField(max_length=50)
    cifrado = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(tamano_bytes__gt=0), name="respaldo_tamano_positivo")
        ]
        indexes = [models.Index(fields=("finca", "creado_en"), name="respaldo_finca_creado_idx")]
