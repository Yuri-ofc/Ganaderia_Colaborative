import uuid

from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel


class Farm(UUIDTimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_farms")
    name = models.CharField(max_length=120)
    location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class FarmMembership(UUIDTimeStampedModel):
    class Role(models.TextChoices):
        ADMINISTRATOR = "administrator", "Administrador"
        OPERATOR = "operator", "Operario"

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="farm_memberships")
    role = models.CharField(max_length=20, choices=Role.choices)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sent_membership_invitations")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("farm", "user"),
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_farm_membership",
            ),
        ]


class Invitation(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        ACCEPTED = "accepted", "Aceptada"
        CANCELLED = "cancelled", "Cancelada"
        EXPIRED = "expired", "Expirada"

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="invitations")
    phone_number = models.CharField(max_length=20)
    role = models.CharField(max_length=20, choices=FarmMembership.Role.choices)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    expires_at = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_invitations")
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="accepted_invitations"
    )
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("farm", "phone_number"),
                condition=models.Q(status="pending", deleted_at__isnull=True),
                name="unique_pending_farm_invitation",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status="accepted", accepted_by__isnull=False, accepted_at__isnull=False)
                    | (~models.Q(status="accepted") & models.Q(accepted_by__isnull=True, accepted_at__isnull=True))
                ),
                name="invitation_acceptance_consistent",
            ),
        ]
        indexes = [models.Index(fields=("status", "expires_at"), name="invitation_status_expiry_idx")]
