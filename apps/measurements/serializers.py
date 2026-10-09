from decimal import Decimal

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from apps.cattle.models import Cattle
from apps.cattle.serializers import accessible_cattle
from apps.common.serializers import (
    CreateOnlyModelSerializer,
    ScopedPrimaryKeyRelatedField,
    current_user,
    require_farm_access,
    require_staff,
)

from .models import AIModel, Device, Measurement, MeasurementType, MorphometricMeasurement, ScaleWeighing


def own_devices(user):
    return Device.objects.filter(owner=user, deleted_at__isnull=True)


def accessible_measurements(user):
    return Measurement.objects.filter(cattle__in=accessible_cattle(user), deleted_at__isnull=True)


def accessible_weighings(user):
    return ScaleWeighing.objects.filter(cattle__in=accessible_cattle(user), deleted_at__isnull=True)


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ("id", "owner", "model_name", "operating_system", "last_connected_at", "created_at", "updated_at")
        read_only_fields = ("id", "owner", "last_connected_at", "created_at", "updated_at")

    def validate(self, attrs):
        user = current_user(self)
        if self.instance and self.instance.owner_id != user.pk:
            raise PermissionDenied("Este dispositivo pertenece a otro usuario.")
        return attrs

    def create(self, validated_data):
        return super().create({**validated_data, "owner": current_user(self)})


class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = ("id", "version", "calibration", "active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        require_staff(self)
        return attrs


class MeasurementTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementType
        fields = ("id", "name", "unit", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        require_staff(self)
        return attrs


class MeasurementSerializer(CreateOnlyModelSerializer):
    cattle = ScopedPrimaryKeyRelatedField(queryset=Cattle.objects.all(), scope=accessible_cattle)
    device = ScopedPrimaryKeyRelatedField(queryset=Device.objects.all(), scope=own_devices)
    ai_model = serializers.PrimaryKeyRelatedField(queryset=AIModel.objects.filter(active=True, deleted_at__isnull=True))
    corrects = ScopedPrimaryKeyRelatedField(
        queryset=Measurement.objects.all(), scope=accessible_measurements, allow_null=True, required=False
    )

    class Meta:
        model = Measurement
        fields = (
            "id", "cattle", "created_by", "device", "ai_model", "captured_at", "capture_mode",
            "estimated_weight_kg", "confidence_interval_min_kg", "confidence_interval_max_kg",
            "body_condition_score", "confidence_level", "corrects", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def validate(self, attrs):
        cattle = attrs.get("cattle", getattr(self.instance, "cattle", None))
        require_farm_access(self, cattle.farm)
        estimate = attrs.get("estimated_weight_kg", getattr(self.instance, "estimated_weight_kg", None))
        lower = attrs.get("confidence_interval_min_kg", getattr(self.instance, "confidence_interval_min_kg", None))
        upper = attrs.get("confidence_interval_max_kg", getattr(self.instance, "confidence_interval_max_kg", None))
        if estimate <= 0 or lower < 0 or upper < lower or not lower <= estimate <= upper:
            raise serializers.ValidationError({"estimated_weight_kg": "El peso debe ser positivo y estar dentro del intervalo válido."})
        if attrs.get("body_condition_score", getattr(self.instance, "body_condition_score", None)) <= 0:
            raise serializers.ValidationError({"body_condition_score": "Debe ser positivo."})
        confidence = attrs.get("confidence_level", getattr(self.instance, "confidence_level", None))
        if not Decimal("0") <= confidence <= Decimal("100"):
            raise serializers.ValidationError({"confidence_level": "Debe estar entre 0 y 100."})
        corrects = attrs.get("corrects")
        if corrects and corrects.cattle_id != cattle.pk:
            raise serializers.ValidationError({"corrects": "La corrección debe referirse al mismo bovino."})
        return attrs

    def create(self, validated_data):
        return super().create({**validated_data, "created_by": current_user(self)})


class MorphometricMeasurementSerializer(CreateOnlyModelSerializer):
    measurement = ScopedPrimaryKeyRelatedField(
        queryset=Measurement.objects.all(), scope=accessible_measurements
    )
    measurement_type = serializers.PrimaryKeyRelatedField(
        queryset=MeasurementType.objects.filter(deleted_at__isnull=True)
    )

    class Meta:
        model = MorphometricMeasurement
        fields = ("id", "measurement", "measurement_type", "value", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        measurement = attrs.get("measurement", getattr(self.instance, "measurement", None))
        require_farm_access(self, measurement.cattle.farm)
        if attrs.get("value", getattr(self.instance, "value", None)) < 0:
            raise serializers.ValidationError({"value": "No puede ser negativo."})
        measurement_type = attrs.get("measurement_type", getattr(self.instance, "measurement_type", None))
        existing = MorphometricMeasurement.objects.filter(
            measurement=measurement, measurement_type=measurement_type, deleted_at__isnull=True
        )
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError({"measurement_type": "Este tipo ya existe en la medición."})
        return attrs


class ScaleWeighingSerializer(CreateOnlyModelSerializer):
    cattle = ScopedPrimaryKeyRelatedField(queryset=Cattle.objects.all(), scope=accessible_cattle)
    corrects = ScopedPrimaryKeyRelatedField(
        queryset=ScaleWeighing.objects.all(), scope=accessible_weighings, allow_null=True, required=False
    )

    class Meta:
        model = ScaleWeighing
        fields = ("id", "cattle", "created_by", "weighed_at", "scale_type", "actual_weight_kg", "corrects", "created_at", "updated_at")
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def validate(self, attrs):
        cattle = attrs.get("cattle", getattr(self.instance, "cattle", None))
        require_farm_access(self, cattle.farm)
        weight = attrs.get("actual_weight_kg", getattr(self.instance, "actual_weight_kg", None))
        if weight <= 0:
            raise serializers.ValidationError({"actual_weight_kg": "El peso debe ser positivo."})
        corrects = attrs.get("corrects")
        if corrects and corrects.cattle_id != cattle.pk:
            raise serializers.ValidationError({"corrects": "La corrección debe referirse al mismo bovino."})
        return attrs

    def create(self, validated_data):
        return super().create({**validated_data, "created_by": current_user(self)})
