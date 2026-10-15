from django.conf import settings
from django.db import models

from apps.common.models import ModeloBaseUuid
from apps.farms.models import Finca


class Raza(ModeloBaseUuid):
    nombre = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("nombre",),
                condition=models.Q(eliminado_en__isnull=True),
                name="raza_activa_nombre_unico",
            ),
        ]

    def __str__(self):
        return self.nombre


class Potrero(ModeloBaseUuid):
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, related_name="potreros")
    nombre = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("finca", "nombre"),
                condition=models.Q(eliminado_en__isnull=True),
                name="potrero_activo_unico_por_finca",
            ),
        ]

    def __str__(self):
        return self.nombre


class Bovino(ModeloBaseUuid):
    class Sexo(models.TextChoices):
        HEMBRA = "hembra", "Hembra"
        MACHO = "macho", "Macho"

    class EstadoOperativo(models.TextChoices):
        PERFIL_PENDIENTE = "perfil_pendiente", "Pendiente de perfil"
        ACTIVO = "activo", "Activo"
        VENDIDO = "vendido", "Vendido"
        MUERTO = "muerto", "Muerto"
        RETIRADO = "retirado", "Retirado"

    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, related_name="bovinos")
    potrero = models.ForeignKey(Potrero, on_delete=models.PROTECT, related_name="bovinos")
    arete = models.CharField(max_length=50)
    raza = models.ForeignKey(Raza, on_delete=models.PROTECT, related_name="bovinos")
    sexo = models.CharField(max_length=10, choices=Sexo.choices)
    categoria_productiva = models.CharField(max_length=100)
    estado_fisiologico = models.CharField(max_length=100, blank=True)
    fecha_nacimiento_estimada = models.DateField(null=True, blank=True)
    estado_operativo = models.CharField(
        max_length=20, choices=EstadoOperativo.choices, default=EstadoOperativo.PERFIL_PENDIENTE
    )
    url_foto_perfil = models.URLField(blank=True)
    perfil_aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="perfiles_aprobados",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bovinos_creados"
    )
    desactivado_en = models.DateTimeField(null=True, blank=True)
    motivo_desactivacion = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("finca", "arete"),
                condition=models.Q(eliminado_en__isnull=True),
                name="arete_activo_unico_por_finca",
            ),
            models.CheckConstraint(
                condition=models.Q(desactivado_en__isnull=True) | ~models.Q(motivo_desactivacion=""),
                name="bovino_desactivacion_con_motivo",
            ),
        ]
        indexes = [models.Index(fields=("finca", "estado_operativo"), name="bovino_finca_estado_idx")]

    def __str__(self):
        return self.arete


class MovimientoPotrero(ModeloBaseUuid):
    bovino = models.ForeignKey(Bovino, on_delete=models.CASCADE, related_name="movimientos")
    potrero = models.ForeignKey(Potrero, on_delete=models.PROTECT, related_name="movimientos")
    iniciado_en = models.DateTimeField()
    finalizado_en = models.DateTimeField(null=True, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="movimientos_creados"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(finalizado_en__isnull=True)
                | models.Q(finalizado_en__gte=models.F("iniciado_en")),
                name="movimiento_fechas_ordenadas",
            ),
            models.UniqueConstraint(
                fields=("bovino",),
                condition=models.Q(finalizado_en__isnull=True, eliminado_en__isnull=True),
                name="movimiento_abierto_unico",
            ),
        ]
        indexes = [models.Index(fields=("bovino", "iniciado_en"), name="movimiento_bovino_inicio_idx")]
