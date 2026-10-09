from django.conf import settings
from django.db import models

from apps.cattle.models import Cattle
from apps.common.models import UUIDTimeStampedModel


class Device(UUIDTimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="devices")
    model_name = models.CharField(max_length=100)
    operating_system = models.CharField(max_length=100)
    last_connected_at = models.DateTimeField(null=True, blank=True)


class AIModel(UUIDTimeStampedModel):
    version = models.CharField(max_length=100, unique=True)
    calibration = models.CharField(max_length=255)
    active = models.BooleanField(default=True)


class MeasurementType(UUIDTimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=20)


class Measurement(UUIDTimeStampedModel):
    class CaptureMode(models.TextChoices):
        VIDEO = "video", "Video"
        PHOTO = "photo", "Foto"

    cattle = models.ForeignKey(Cattle, on_delete=models.PROTECT, related_name="measurements")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="measurements")
    device = models.ForeignKey(Device, on_delete=models.PROTECT, related_name="measurements")
    ai_model = models.ForeignKey(AIModel, on_delete=models.PROTECT, related_name="measurements")
    captured_at = models.DateTimeField()
    capture_mode = models.CharField(max_length=10, choices=CaptureMode.choices)
    estimated_weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
    confidence_interval_min_kg = models.DecimalField(max_digits=6, decimal_places=2)
    confidence_interval_max_kg = models.DecimalField(max_digits=6, decimal_places=2)
    body_condition_score = models.DecimalField(max_digits=3, decimal_places=1)
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2)
    corrects = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, related_name="corrections")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(estimated_weight_kg__gt=0), name="measurement_positive_weight"),
            models.CheckConstraint(
                condition=models.Q(confidence_interval_min_kg__gte=0)
                & models.Q(confidence_interval_max_kg__gte=models.F("confidence_interval_min_kg"))
                & models.Q(estimated_weight_kg__gte=models.F("confidence_interval_min_kg"))
                & models.Q(estimated_weight_kg__lte=models.F("confidence_interval_max_kg")),
                name="measurement_confidence_interval_valid",
            ),
            models.CheckConstraint(condition=models.Q(body_condition_score__gt=0), name="measurement_positive_body_score"),
            models.CheckConstraint(condition=models.Q(confidence_level__gte=0), name="measurement_nonnegative_confidence"),
        ]
        indexes = [models.Index(fields=("cattle", "captured_at"), name="measurement_cattle_capture_idx")]


class MorphometricMeasurement(UUIDTimeStampedModel):
    measurement = models.ForeignKey(Measurement, on_delete=models.CASCADE, related_name="morphometrics")
    measurement_type = models.ForeignKey(MeasurementType, on_delete=models.PROTECT, related_name="records")
    value = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("measurement", "measurement_type"),
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_morphometric_type",
            ),
            models.CheckConstraint(condition=models.Q(value__gte=0), name="morphometric_nonnegative_value"),
        ]


class ScaleWeighing(UUIDTimeStampedModel):
    cattle = models.ForeignKey(Cattle, on_delete=models.PROTECT, related_name="scale_weighings")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="scale_weighings")
    weighed_at = models.DateTimeField()
    scale_type = models.CharField(max_length=100)
    actual_weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
    corrects = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, related_name="corrections")

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(actual_weight_kg__gt=0), name="scale_weighing_positive_weight")]
        indexes = [models.Index(fields=("cattle", "weighed_at"), name="scale_weighing_cattle_date_idx")]
