from django.utils import timezone
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.common.serializers import accessible_farms, managed_farms, require_farm_access
from apps.common.views import SoftDeleteMixin, StaffWritePermissionMixin, uuid_query_param

from .models import Breed, Cattle, Lot, LotMovement
from .serializers import BreedSerializer, CattleSerializer, LotMovementSerializer, LotSerializer


class BreedViewSet(StaffWritePermissionMixin, SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = BreedSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)

    def get_queryset(self):
        return Breed.objects.filter(deleted_at__isnull=True).order_by("name", "id")

    def perform_destroy(self, instance):
        if instance.cattle.filter(deleted_at__isnull=True).exists():
            raise ValidationError("La raza está asociada a bovinos activos.")
        super().perform_destroy(instance)


class LotViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = LotSerializer

    def get_queryset(self):
        queryset = Lot.objects.filter(
            farm__in=accessible_farms(self.request.user), deleted_at__isnull=True
        ).select_related("farm")
        farm_id = uuid_query_param(self.request, "farm")
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        return queryset.order_by("name", "id")

    def perform_destroy(self, instance):
        require_farm_access(self.get_serializer(), instance.farm, manage=True)
        if instance.cattle.filter(deleted_at__isnull=True).exists():
            raise ValidationError("El lote contiene bovinos activos.")
        super().perform_destroy(instance)


class CattleViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = CattleSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("ear_tag", "breed__name", "lot__name")
    ordering_fields = ("ear_tag", "created_at", "estimated_birth_date")
    ordering = ("ear_tag", "id")

    def get_queryset(self):
        queryset = Cattle.objects.filter(
            farm__in=accessible_farms(self.request.user), deleted_at__isnull=True
        ).select_related("farm", "lot", "breed", "created_by")
        farm_id = uuid_query_param(self.request, "farm")
        lot_id = uuid_query_param(self.request, "lot")
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        if lot_id:
            queryset = queryset.filter(lot_id=lot_id)
        operational_status = self.request.query_params.get("status")
        if operational_status:
            if operational_status not in Cattle.OperationalStatus.values:
                raise ValidationError({"status": "Estado operativo inválido."})
            queryset = queryset.filter(operational_status=operational_status)
        return queryset

    def perform_destroy(self, instance):
        require_farm_access(self.get_serializer(), instance.farm, manage=True)
        super().perform_destroy(instance)

    @action(detail=True, methods=("post",), url_path="approve-profile")
    def approve_profile(self, request, pk=None):
        cattle = self.get_object()
        require_farm_access(self.get_serializer(), cattle.farm, manage=True)
        if cattle.operational_status != Cattle.OperationalStatus.PENDING_PROFILE:
            raise ValidationError("Solo se pueden aprobar perfiles pendientes.")
        cattle.operational_status = Cattle.OperationalStatus.ACTIVE
        cattle.profile_approved_by = request.user
        cattle.save(update_fields=("operational_status", "profile_approved_by", "updated_at"))
        return Response(self.get_serializer(cattle).data)

    @action(detail=True, methods=("post",))
    def deactivate(self, request, pk=None):
        cattle = self.get_object()
        require_farm_access(self.get_serializer(), cattle.farm, manage=True)
        new_status = request.data.get("status")
        reason = request.data.get("reason", "")
        allowed = {
            Cattle.OperationalStatus.SOLD,
            Cattle.OperationalStatus.DECEASED,
            Cattle.OperationalStatus.RETIRED,
        }
        if new_status not in allowed:
            raise ValidationError({"status": "Use sold, deceased o retired."})
        if not isinstance(reason, str) or not reason.strip():
            raise ValidationError({"reason": "Debe indicar el motivo de baja."})
        reason = reason.strip()
        if len(reason) > 255:
            raise ValidationError({"reason": "El motivo no puede superar 255 caracteres."})
        if cattle.deactivated_at is not None:
            raise ValidationError("El bovino ya fue dado de baja.")
        cattle.operational_status = new_status
        cattle.deactivated_at = timezone.now()
        cattle.deactivation_reason = reason
        cattle.save(update_fields=("operational_status", "deactivated_at", "deactivation_reason", "updated_at"))
        return Response(self.get_serializer(cattle).data, status=status.HTTP_200_OK)


class LotMovementViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = LotMovementSerializer
    http_method_names = ("get", "post", "patch", "head", "options")

    def get_queryset(self):
        queryset = LotMovement.objects.filter(
            cattle__farm__in=accessible_farms(self.request.user),
            cattle__deleted_at__isnull=True,
            deleted_at__isnull=True,
        ).select_related("cattle", "lot", "created_by")
        cattle_id = uuid_query_param(self.request, "cattle")
        if cattle_id:
            queryset = queryset.filter(cattle_id=cattle_id)
        return queryset.order_by("-started_at", "-id")
