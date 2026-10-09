from uuid import UUID

from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission, IsAdminUser, SAFE_METHODS


def uuid_query_param(request, name):
    value = request.query_params.get(name)
    if value is None or value == "":
        return None
    try:
        return UUID(value)
    except (TypeError, ValueError, AttributeError):
        raise ValidationError({name: "Debe ser un UUID válido."})


class SoftDeleteMixin:
    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=("deleted_at", "updated_at"))


class ActiveUserPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.is_active and user.deleted_at is None)


class StaffWritePermissionMixin:
    def get_permissions(self):
        permissions = [ActiveUserPermission()]
        if self.request.method not in SAFE_METHODS:
            permissions.append(IsAdminUser())
        return permissions
