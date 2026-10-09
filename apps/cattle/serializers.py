from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from apps.common.serializers import (
    ScopedPrimaryKeyRelatedField,
    accessible_farms,
    current_user,
    immutable_relation,
    managed_farms,
    require_farm_access,
    require_staff,
)
from apps.farms.models import Farm

from .models import Breed, Cattle, Lot, LotMovement


def accessible_lots(user):
    return Lot.objects.filter(farm__in=accessible_farms(user), deleted_at__isnull=True)


def accessible_cattle(user):
    return Cattle.objects.filter(farm__in=accessible_farms(user), deleted_at__isnull=True)


class BreedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Breed
        fields = ("id", "name", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        require_staff(self)
        name = attrs.get("name", getattr(self.instance, "name", None))
        existing = Breed.objects.filter(name=name, deleted_at__isnull=True)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError({"name": "Esta raza ya existe."})
        return attrs


class LotSerializer(serializers.ModelSerializer):
    farm = ScopedPrimaryKeyRelatedField(queryset=Farm.objects.all(), scope=managed_farms)

    class Meta:
        model = Lot
        fields = ("id", "farm", "name", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        farm = self.instance.farm if self.instance else attrs["farm"]
        require_farm_access(self, farm, manage=True)
        if self.instance:
            immutable_relation(attrs, self.instance, "farm")
        name = attrs.get("name", getattr(self.instance, "name", None))
        existing = Lot.objects.filter(farm=farm, name=name, deleted_at__isnull=True)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError({"name": "Ya existe un lote con este nombre en la finca."})
        return attrs


class CattleSerializer(serializers.ModelSerializer):
    farm = ScopedPrimaryKeyRelatedField(queryset=Farm.objects.all(), scope=accessible_farms)
    lot = ScopedPrimaryKeyRelatedField(queryset=Lot.objects.all(), scope=accessible_lots)
    breed = serializers.PrimaryKeyRelatedField(queryset=Breed.objects.filter(deleted_at__isnull=True))

    class Meta:
        model = Cattle
        fields = (
            "id", "farm", "lot", "ear_tag", "breed", "sex", "productive_category",
            "physiological_status", "estimated_birth_date", "operational_status", "profile_photo_url",
            "profile_approved_by", "created_by", "deactivated_at", "deactivation_reason",
            "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "operational_status", "profile_approved_by", "created_by",
            "deactivated_at", "deactivation_reason", "created_at", "updated_at",
        )

    def validate(self, attrs):
        farm = self.instance.farm if self.instance else attrs["farm"]
        require_farm_access(self, farm)
        if self.instance:
            immutable_relation(attrs, self.instance, "farm")
            immutable_relation(attrs, self.instance, "lot")
        lot = attrs.get("lot", getattr(self.instance, "lot", None))
        if lot.farm_id != farm.pk:
            raise serializers.ValidationError({"lot": "El lote debe pertenecer a la misma finca."})
        ear_tag = attrs.get("ear_tag", getattr(self.instance, "ear_tag", None))
        existing = Cattle.objects.filter(farm=farm, ear_tag=ear_tag, deleted_at__isnull=True)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError({"ear_tag": "Este arete ya existe en la finca."})
        birth_date = attrs.get("estimated_birth_date", getattr(self.instance, "estimated_birth_date", None))
        if birth_date and birth_date > timezone.localdate():
            raise serializers.ValidationError({"estimated_birth_date": "La fecha no puede ser futura."})
        return attrs

    def create(self, validated_data):
        return super().create({**validated_data, "created_by": current_user(self)})


class LotMovementSerializer(serializers.ModelSerializer):
    cattle = ScopedPrimaryKeyRelatedField(queryset=Cattle.objects.all(), scope=accessible_cattle)
    lot = ScopedPrimaryKeyRelatedField(queryset=Lot.objects.all(), scope=accessible_lots)

    class Meta:
        model = LotMovement
        fields = ("id", "cattle", "lot", "started_at", "ended_at", "created_by", "created_at", "updated_at")
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def validate(self, attrs):
        cattle = self.instance.cattle if self.instance else attrs["cattle"]
        require_farm_access(self, cattle.farm)
        if self.instance:
            for field in ("cattle", "lot"):
                immutable_relation(attrs, self.instance, field)
            if "started_at" in attrs and attrs["started_at"] != self.instance.started_at:
                raise serializers.ValidationError({"started_at": "La fecha inicial no se puede cambiar."})
        lot = attrs.get("lot", getattr(self.instance, "lot", None))
        if lot.farm_id != cattle.farm_id:
            raise serializers.ValidationError({"lot": "El lote debe pertenecer a la finca del bovino."})
        started_at = attrs.get("started_at", getattr(self.instance, "started_at", None))
        ended_at = attrs.get("ended_at", getattr(self.instance, "ended_at", None))
        if ended_at is not None and ended_at < started_at:
            raise serializers.ValidationError({"ended_at": "Debe ser posterior al inicio."})
        if ended_at is None and started_at > timezone.now():
            raise serializers.ValidationError({"started_at": "Un movimiento abierto no puede iniciar en el futuro."})
        if self.instance and self.instance.ended_at is not None and ended_at != self.instance.ended_at:
            raise serializers.ValidationError({"ended_at": "Un movimiento cerrado es inmutable."})
        overlapping = LotMovement.objects.filter(cattle=cattle, deleted_at__isnull=True).filter(
            Q(ended_at__isnull=True) | Q(ended_at__gt=started_at)
        )
        if ended_at is not None:
            overlapping = overlapping.filter(started_at__lt=ended_at)
        if self.instance:
            overlapping = overlapping.exclude(pk=self.instance.pk)
        if overlapping.exists():
            raise serializers.ValidationError("El periodo se superpone con otro movimiento del bovino.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        movement = super().create({**validated_data, "created_by": current_user(self)})
        if movement.ended_at is None:
            Cattle.objects.filter(pk=movement.cattle_id).update(lot=movement.lot, updated_at=timezone.now())
        return movement
