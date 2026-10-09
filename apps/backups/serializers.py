from rest_framework import serializers

from apps.common.serializers import (
    CreateOnlyModelSerializer,
    ScopedPrimaryKeyRelatedField,
    current_user,
    managed_farms,
    require_farm_access,
)
from apps.farms.models import Farm

from .models import Backup


class BackupSerializer(CreateOnlyModelSerializer):
    farm = ScopedPrimaryKeyRelatedField(queryset=Farm.objects.all(), scope=managed_farms)

    class Meta:
        model = Backup
        fields = (
            "id", "farm", "created_by", "storage_url", "checksum", "size_bytes",
            "version", "encrypted", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def validate(self, attrs):
        farm = self.instance.farm if self.instance else attrs["farm"]
        require_farm_access(self, farm, manage=True)
        if attrs.get("size_bytes", getattr(self.instance, "size_bytes", None)) <= 0:
            raise serializers.ValidationError({"size_bytes": "El archivo debe tener un tamaño positivo."})
        return attrs

    def create(self, validated_data):
        return super().create({**validated_data, "created_by": current_user(self)})
