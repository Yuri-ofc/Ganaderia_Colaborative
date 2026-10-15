from django.conf import settings
from django.db import models

from apps.cattle.models import Bovino
from apps.common.models import ModeloBaseUuid


class Dispositivo(ModeloBaseUuid):
    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="dispositivos"
    )
    modelo = models.CharField(max_length=100)
    sistema_operativo = models.CharField(max_length=100)
    ultima_conexion_en = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.modelo


class ModeloIa(ModeloBaseUuid):
    version = models.CharField(max_length=100, unique=True)
    calibracion = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.version


class TipoMedida(ModeloBaseUuid):
    nombre = models.CharField(max_length=100, unique=True)
    unidad = models.CharField(max_length=20)

    def __str__(self):
        return self.nombre


class Medicion(ModeloBaseUuid):
    class ModoCaptura(models.TextChoices):
        VIDEO = "video", "Video"
        FOTO = "foto", "Foto"

    bovino = models.ForeignKey(Bovino, on_delete=models.PROTECT, related_name="mediciones")
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="mediciones"
    )
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.PROTECT, related_name="mediciones")
    modelo_ia = models.ForeignKey(ModeloIa, on_delete=models.PROTECT, related_name="mediciones")
    capturado_en = models.DateTimeField()
    modo_captura = models.CharField(max_length=10, choices=ModoCaptura.choices)
    peso_estimado_kg = models.DecimalField(max_digits=6, decimal_places=2)
    intervalo_confianza_min_kg = models.DecimalField(max_digits=6, decimal_places=2)
    intervalo_confianza_max_kg = models.DecimalField(max_digits=6, decimal_places=2)
    condicion_corporal = models.DecimalField(max_digits=3, decimal_places=1)
    nivel_confianza = models.DecimalField(max_digits=5, decimal_places=2)
    corrige = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="correcciones"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(peso_estimado_kg__gt=0), name="medicion_peso_positivo"
            ),
            models.CheckConstraint(
                condition=models.Q(intervalo_confianza_min_kg__gte=0)
                & models.Q(intervalo_confianza_max_kg__gte=models.F("intervalo_confianza_min_kg"))
                & models.Q(peso_estimado_kg__gte=models.F("intervalo_confianza_min_kg"))
                & models.Q(peso_estimado_kg__lte=models.F("intervalo_confianza_max_kg")),
                name="medicion_intervalo_confianza_valido",
            ),
            models.CheckConstraint(
                condition=models.Q(condicion_corporal__gt=0), name="medicion_condicion_positiva"
            ),
            models.CheckConstraint(
                condition=models.Q(nivel_confianza__gte=0), name="medicion_confianza_no_negativa"
            ),
        ]
        indexes = [models.Index(fields=("bovino", "capturado_en"), name="medicion_bovino_captura_idx")]


class MedidaMorfometrica(ModeloBaseUuid):
    medicion = models.ForeignKey(
        Medicion, on_delete=models.CASCADE, related_name="medidas_morfometricas"
    )
    tipo_medida = models.ForeignKey(TipoMedida, on_delete=models.PROTECT, related_name="registros")
    valor = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("medicion", "tipo_medida"),
                condition=models.Q(eliminado_en__isnull=True),
                name="medida_morfometrica_tipo_unico",
            ),
            models.CheckConstraint(
                condition=models.Q(valor__gte=0), name="medida_morfometrica_valor_no_negativo"
            ),
        ]


class Pesaje(ModeloBaseUuid):
    bovino = models.ForeignKey(Bovino, on_delete=models.PROTECT, related_name="pesajes")
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pesajes"
    )
    pesado_en = models.DateTimeField()
    tipo_bascula = models.CharField(max_length=100)
    peso_real_kg = models.DecimalField(max_digits=6, decimal_places=2)
    corrige = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="correcciones"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(peso_real_kg__gt=0), name="pesaje_peso_positivo")
        ]
        indexes = [models.Index(fields=("bovino", "pesado_en"), name="pesaje_bovino_fecha_idx")]
