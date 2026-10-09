from rest_framework import mixins, viewsets

from apps.common.serializers import managed_farms
from apps.common.views import uuid_query_param

from .models import Backup
from .serializers import BackupSerializer


class BackupViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = BackupSerializer

    def get_queryset(self):
        queryset = Backup.objects.filter(
            farm__in=managed_farms(self.request.user), deleted_at__isnull=True
        ).select_related("farm", "created_by")
        farm_id = uuid_query_param(self.request, "farm")
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        return queryset.order_by("-created_at", "-id")
