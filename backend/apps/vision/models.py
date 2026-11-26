from django.conf import settings
from django.db import models

from apps.cattle.models import Bovino
from apps.common.models import ModeloBaseUuid
from apps.measurements.models import Medicion


class CapturaVision(ModeloBaseUuid):
    """Foto o video de un bovino y la medición que se estimó a partir de ella."""

    class TipoArchivo(models.TextChoices):
        FOTO = "foto", "Foto"
        VIDEO = "video", "Video"

    bovino = models.ForeignKey(Bovino, on_delete=models.PROTECT, related_name="capturas_vision")
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="capturas_vision"
    )
    archivo = models.FileField(upload_to="vision/capturas/%Y/%m/")
    tipo_archivo = models.CharField(max_length=10, choices=TipoArchivo.choices)
    medicion = models.OneToOneField(
        Medicion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="captura_vision",
    )

    class Meta:
        indexes = [models.Index(fields=("bovino", "creado_en"), name="captura_bovino_creado_idx")]

    def __str__(self):
        return f"Captura de {self.bovino.arete}"
