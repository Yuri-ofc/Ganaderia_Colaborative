from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from apps.common.serializers import (
    ScopedPrimaryKeyRelatedField,
    current_user,
    immutable_relation,
    managed_farms,
    require_farm_access,
)

from .models import Farm, FarmMembership, Invitation

User = get_user_model()


class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = ("id", "owner", "name", "location", "created_at", "updated_at")
        read_only_fields = ("id", "owner", "created_at", "updated_at")

    def validate(self, attrs):
        user = current_user(self)
        if self.instance and self.instance.owner_id != user.pk:
            raise PermissionDenied("Solo el propietario puede modificar la finca.")
        return attrs

    def create(self, validated_data):
        return super().create({**validated_data, "owner": current_user(self)})


class FarmMembershipSerializer(serializers.ModelSerializer):
    farm = ScopedPrimaryKeyRelatedField(queryset=Farm.objects.all(), scope=managed_farms)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(deleted_at__isnull=True))

    class Meta:
        model = FarmMembership
        fields = ("id", "farm", "user", "role", "invited_by", "created_at", "updated_at")
        read_only_fields = ("id", "invited_by", "created_at", "updated_at")

    def validate(self, attrs):
        actor = current_user(self)
        farm = self.instance.farm if self.instance else attrs["farm"]
        require_farm_access(self, farm, manage=True)
        if self.instance:
            immutable_relation(attrs, self.instance, "farm")
            immutable_relation(attrs, self.instance, "user")
        member = attrs.get("user", getattr(self.instance, "user", None))
        role = attrs.get("role", getattr(self.instance, "role", None))
        if member.pk == farm.owner_id:
            raise serializers.ValidationError({"user": "El propietario ya administra la finca."})
        if (
            role == FarmMembership.Role.ADMINISTRATOR
            or (self.instance and self.instance.role == FarmMembership.Role.ADMINISTRATOR)
        ) and farm.owner_id != actor.pk:
            raise PermissionDenied("Solo el propietario puede asignar el rol de administrador.")
        existing = FarmMembership.objects.filter(farm=farm, user=member, deleted_at__isnull=True)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError({"user": "Este usuario ya es miembro activo de la finca."})
        return attrs

    def create(self, validated_data):
        return super().create({**validated_data, "invited_by": current_user(self)})


class InvitationSerializer(serializers.ModelSerializer):
    farm = ScopedPrimaryKeyRelatedField(queryset=Farm.objects.all(), scope=managed_farms)
    status = serializers.ChoiceField(choices=Invitation.Status.choices, required=False)

    class Meta:
        model = Invitation
        fields = (
            "id", "farm", "phone_number", "role", "token", "status", "expires_at",
            "created_by", "accepted_by", "accepted_at", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "token", "created_by", "accepted_by", "accepted_at", "created_at", "updated_at",
        )

    def validate(self, attrs):
        actor = current_user(self)
        farm = self.instance.farm if self.instance else attrs["farm"]
        require_farm_access(self, farm, manage=True)
        if self.instance:
            immutable_relation(attrs, self.instance, "farm")
            if self.instance.status != Invitation.Status.PENDING:
                raise serializers.ValidationError("Solo se pueden modificar invitaciones pendientes.")
            if attrs.get("status", Invitation.Status.PENDING) not in (
                Invitation.Status.PENDING, Invitation.Status.CANCELLED
            ):
                raise serializers.ValidationError({"status": "Solo se puede cancelar una invitación pendiente."})
        elif attrs.get("status", Invitation.Status.PENDING) != Invitation.Status.PENDING:
            raise serializers.ValidationError({"status": "Las invitaciones nuevas deben quedar pendientes."})
        role = attrs.get("role", getattr(self.instance, "role", None))
        if role == FarmMembership.Role.ADMINISTRATOR and farm.owner_id != actor.pk:
            raise PermissionDenied("Solo el propietario puede invitar administradores.")
        expires_at = attrs.get("expires_at", getattr(self.instance, "expires_at", None))
        status = attrs.get("status", getattr(self.instance, "status", Invitation.Status.PENDING))
        if status == Invitation.Status.PENDING and expires_at <= timezone.now():
            raise serializers.ValidationError({"expires_at": "La fecha de vencimiento debe ser futura."})
        phone_number = attrs.get("phone_number", getattr(self.instance, "phone_number", None))
        if status == Invitation.Status.PENDING:
            existing = Invitation.objects.filter(
                farm=farm, phone_number=phone_number, status=Invitation.Status.PENDING, deleted_at__isnull=True
            )
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError({"phone_number": "Ya hay una invitación pendiente para este teléfono."})
        return attrs

    def create(self, validated_data):
        return super().create({**validated_data, "created_by": current_user(self)})
