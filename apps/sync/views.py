from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.common.serializers import accessible_farms
from apps.common.views import uuid_query_param

from .models import SyncChange
from .serializers import SyncChangeSerializer


class SyncChangeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SyncChangeSerializer

    def get_queryset(self):
        queryset = SyncChange.objects.filter(
            farm__in=accessible_farms(self.request.user), deleted_at__isnull=True
        ).select_related("farm", "device", "created_by")
        farm_id = uuid_query_param(self.request, "farm")
        device_id = uuid_query_param(self.request, "device")
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        return queryset.order_by("-created_at", "-id")

    @action(detail=True, methods=("post",))
    def acknowledge(self, request, pk=None):
        change = self.get_object()
        if change.device.owner_id != request.user.pk:
            raise PermissionDenied("Solo el propietario del dispositivo puede confirmar este cambio.")
        if change.synchronized_at is None:
            change.synchronized_at = timezone.now()
            change.save(update_fields=("synchronized_at", "updated_at"))
        return Response(self.get_serializer(change).data)
