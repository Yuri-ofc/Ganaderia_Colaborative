from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from apps.farms.models import Farm, FarmMembership


def current_user(serializer):
    request = serializer.context.get("request")
    if (
        request is None
        or not request.user.is_authenticated
        or not request.user.is_active
        or request.user.deleted_at is not None
    ):
        raise PermissionDenied("Se requiere un usuario autenticado en el contexto del serializer.")
    return request.user


def accessible_farms(user):
    if user is None or not user.is_authenticated or not user.is_active or user.deleted_at is not None:
        return Farm.objects.none()
    return Farm.objects.filter(deleted_at__isnull=True).filter(
        Q(owner=user)
        | Q(memberships__user=user, memberships__deleted_at__isnull=True)
    ).distinct()


def managed_farms(user):
    if user is None or not user.is_authenticated or not user.is_active or user.deleted_at is not None:
        return Farm.objects.none()
    return Farm.objects.filter(deleted_at__isnull=True).filter(
        Q(owner=user)
        | Q(
            memberships__user=user,
            memberships__role=FarmMembership.Role.ADMINISTRATOR,
            memberships__deleted_at__isnull=True,
        )
    ).distinct()


def require_farm_access(serializer, farm, *, manage=False):
    user = current_user(serializer)
    farms = managed_farms(user) if manage else accessible_farms(user)
    if not farms.filter(pk=farm.pk).exists():
        raise PermissionDenied("No tiene permiso sobre esta finca.")
    return user


def require_staff(serializer):
    user = current_user(serializer)
    if not user.is_staff:
        raise PermissionDenied("Solo el personal autorizado puede modificar este catálogo.")
    return user


def immutable_relation(attrs, instance, field):
    value = attrs.get(field)
    if value is not None and value.pk != getattr(instance, f"{field}_id"):
        raise serializers.ValidationError({field: "Esta relación no se puede cambiar."})


class ScopedPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """Resolve foreign keys only inside the authenticated user's allowed queryset."""

    def __init__(self, *, scope, **kwargs):
        self.scope = scope
        super().__init__(**kwargs)

    def get_queryset(self):
        request = self.context.get("request")
        if (
            request is None
            or not request.user.is_authenticated
            or not request.user.is_active
            or request.user.deleted_at is not None
        ):
            return super().get_queryset().none()
        return self.scope(request.user)


class CreateOnlyModelSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        raise PermissionDenied("Este registro histórico es inmutable; cree una corrección nueva.")
