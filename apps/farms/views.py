from uuid import UUID

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.common.serializers import accessible_farms, managed_farms
from apps.common.views import SoftDeleteMixin, uuid_query_param

from .models import Farm, FarmMembership, Invitation
from .serializers import FarmMembershipSerializer, FarmSerializer, InvitationSerializer


class FarmViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = FarmSerializer

    def get_queryset(self):
        return accessible_farms(self.request.user).select_related("owner").order_by("name", "id")

    def perform_destroy(self, instance):
        if instance.owner_id != self.request.user.pk:
            raise PermissionDenied("Solo el propietario puede eliminar la finca.")
        super().perform_destroy(instance)


class MembershipViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = FarmMembershipSerializer

    def get_queryset(self):
        queryset = FarmMembership.objects.filter(
            farm__in=managed_farms(self.request.user), deleted_at__isnull=True
        ).select_related("farm", "user", "invited_by")
        farm_id = uuid_query_param(self.request, "farm")
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        return queryset.order_by("-created_at", "-id")

    def perform_destroy(self, instance):
        if instance.role == FarmMembership.Role.ADMINISTRATOR and instance.farm.owner_id != self.request.user.pk:
            raise PermissionDenied("Solo el propietario puede retirar administradores.")
        super().perform_destroy(instance)


class InvitationViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = InvitationSerializer

    def get_queryset(self):
        queryset = Invitation.objects.filter(
            farm__in=managed_farms(self.request.user), deleted_at__isnull=True
        ).select_related("farm", "created_by", "accepted_by")
        farm_id = uuid_query_param(self.request, "farm")
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        return queryset.order_by("-created_at", "-id")

    def perform_destroy(self, instance):
        if instance.status != Invitation.Status.PENDING:
            raise ValidationError("Solo se pueden cancelar invitaciones pendientes.")
        if instance.role == FarmMembership.Role.ADMINISTRATOR and instance.farm.owner_id != self.request.user.pk:
            raise PermissionDenied("Solo el propietario puede cancelar invitaciones de administrador.")
        instance.status = Invitation.Status.CANCELLED
        instance.deleted_at = timezone.now()
        instance.save(update_fields=("status", "deleted_at", "updated_at"))

    @action(detail=False, methods=("post",), url_path="accept")
    def accept(self, request):
        token = request.data.get("token")
        if not token:
            raise ValidationError({"token": "Este campo es obligatorio."})
        try:
            token_id = UUID(str(token))
        except (TypeError, ValueError, AttributeError):
            raise ValidationError({"token": "Debe ser un UUID válido."})
        with transaction.atomic():
            invitation = Invitation.objects.select_for_update().filter(
                token=token_id, status=Invitation.Status.PENDING, deleted_at__isnull=True,
                farm__deleted_at__isnull=True,
            ).select_related("farm").first()
            if invitation is None:
                raise ValidationError({"token": "Invitación inválida o ya utilizada."})
            if invitation.expires_at <= timezone.now():
                invitation.status = Invitation.Status.EXPIRED
                invitation.save(update_fields=("status", "updated_at"))
                return Response({"token": ["La invitación ha vencido."]}, status=status.HTTP_400_BAD_REQUEST)
            if not request.user.phone_number or request.user.phone_number != invitation.phone_number:
                raise PermissionDenied("La invitación corresponde a otro número de teléfono.")
            if invitation.farm.owner_id == request.user.pk:
                raise ValidationError({"token": "El propietario ya pertenece a la finca."})
            membership, created = FarmMembership.objects.get_or_create(
                farm=invitation.farm,
                user=request.user,
                deleted_at__isnull=True,
                defaults={"role": invitation.role, "invited_by": invitation.created_by},
            )
            invitation.status = Invitation.Status.ACCEPTED
            invitation.accepted_by = request.user
            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=("status", "accepted_by", "accepted_at", "updated_at"))
        return Response(
            {"membership_id": str(membership.pk), "farm_id": str(invitation.farm_id), "created": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
