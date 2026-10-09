from rest_framework import serializers

from apps.common.serializers import (
    CreateOnlyModelSerializer,
    ScopedPrimaryKeyRelatedField,
    accessible_farms,
    current_user,
    require_farm_access,
)
from apps.farms.models import Farm
from apps.measurements.models import Device
from apps.measurements.serializers import own_devices

from .models import SyncChange


class SyncChangeSerializer(CreateOnlyModelSerializer):
    farm = ScopedPrimaryKeyRelatedField(queryset=Farm.objects.all(), scope=accessible_farms)
    device = ScopedPrimaryKeyRelatedField(queryset=Device.objects.all(), scope=own_devices)

    class Meta:
        model = SyncChange
        fields = (
            "id", "farm", "device", "created_by", "client_change_id", "resource",
            "object_id", "action", "payload", "synchronized_at", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_by", "synchronized_at", "created_at", "updated_at")

    def validate(self, attrs):
        farm = attrs.get("farm", getattr(self.instance, "farm", None))
        require_farm_access(self, farm)
        device = attrs.get("device", getattr(self.instance, "device", None))
        change_id = attrs.get("client_change_id", getattr(self.instance, "client_change_id", None))
        existing = SyncChange.objects.filter(device=device, client_change_id=change_id)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError({"client_change_id": "Este cambio ya fue recibido desde el dispositivo."})
        return attrs

    def create(self, validated_data):
        return super().create({**validated_data, "created_by": current_user(self)})
