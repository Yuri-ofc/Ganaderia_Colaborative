from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel
from apps.farms.models import Farm


class Breed(UUIDTimeStampedModel):
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("name",), condition=models.Q(deleted_at__isnull=True), name="unique_active_breed_name"),
        ]

    def __str__(self):
        return self.name


class Lot(UUIDTimeStampedModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="lots")
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("farm", "name"), condition=models.Q(deleted_at__isnull=True), name="unique_active_lot_per_farm"
            ),
        ]


class Cattle(UUIDTimeStampedModel):
    class Sex(models.TextChoices):
        FEMALE = "female", "Hembra"
        MALE = "male", "Macho"

    class OperationalStatus(models.TextChoices):
        PENDING_PROFILE = "pending_profile", "Pendiente de perfil"
        ACTIVE = "active", "Activo"
        SOLD = "sold", "Vendido"
        DECEASED = "deceased", "Muerto"
        RETIRED = "retired", "Retirado"

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="cattle")
    lot = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name="cattle")
    ear_tag = models.CharField(max_length=50)
    breed = models.ForeignKey(Breed, on_delete=models.PROTECT, related_name="cattle")
    sex = models.CharField(max_length=10, choices=Sex.choices)
    productive_category = models.CharField(max_length=100)
    physiological_status = models.CharField(max_length=100, blank=True)
    estimated_birth_date = models.DateField(null=True, blank=True)
    operational_status = models.CharField(max_length=20, choices=OperationalStatus.choices, default=OperationalStatus.PENDING_PROFILE)
    profile_photo_url = models.URLField(blank=True)
    profile_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="approved_profiles"
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_cattle")
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivation_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("farm", "ear_tag"),
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_ear_tag_per_farm",
            ),
            models.CheckConstraint(
                condition=models.Q(deactivated_at__isnull=True) | ~models.Q(deactivation_reason=""),
                name="cattle_deactivation_has_reason",
            ),
        ]
        indexes = [models.Index(fields=("farm", "operational_status"), name="cattle_farm_status_idx")]


class LotMovement(UUIDTimeStampedModel):
    cattle = models.ForeignKey(Cattle, on_delete=models.CASCADE, related_name="lot_movements")
    lot = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name="movements")
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_lot_movements")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ended_at__isnull=True) | models.Q(ended_at__gte=models.F("started_at")),
                name="lot_movement_dates_ordered",
            ),
            models.UniqueConstraint(
                fields=("cattle",),
                condition=models.Q(ended_at__isnull=True, deleted_at__isnull=True),
                name="unique_open_lot_movement",
            ),
        ]
        indexes = [models.Index(fields=("cattle", "started_at"), name="lot_movement_cattle_start_idx")]
