from rest_framework import filters, mixins, viewsets

from apps.common.serializers import accessible_farms
from apps.common.views import SoftDeleteMixin, StaffWritePermissionMixin, uuid_query_param

from .models import AIModel, Device, Measurement, MeasurementType, MorphometricMeasurement, ScaleWeighing
from .serializers import (
    AIModelSerializer,
    DeviceSerializer,
    MeasurementSerializer,
    MeasurementTypeSerializer,
    MorphometricMeasurementSerializer,
    ScaleWeighingSerializer,
)


class DeviceViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = DeviceSerializer

    def get_queryset(self):
        return Device.objects.filter(
            owner=self.request.user, deleted_at__isnull=True
        ).order_by("-last_connected_at", "-created_at", "-id")


class AIModelViewSet(StaffWritePermissionMixin, SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = AIModelSerializer

    def get_queryset(self):
        return AIModel.objects.filter(deleted_at__isnull=True).order_by("-created_at", "-id")


class MeasurementTypeViewSet(StaffWritePermissionMixin, SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = MeasurementTypeSerializer

    def get_queryset(self):
        return MeasurementType.objects.filter(deleted_at__isnull=True).order_by("name", "id")


class MeasurementViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = MeasurementSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("cattle__ear_tag",)
    ordering_fields = ("captured_at", "created_at")
    ordering = ("-captured_at", "-id")

    def get_queryset(self):
        queryset = Measurement.objects.filter(
            cattle__farm__in=accessible_farms(self.request.user), deleted_at__isnull=True
        ).select_related("cattle", "device", "ai_model", "created_by")
        farm_id = uuid_query_param(self.request, "farm")
        cattle_id = uuid_query_param(self.request, "cattle")
        if farm_id:
            queryset = queryset.filter(cattle__farm_id=farm_id)
        if cattle_id:
            queryset = queryset.filter(cattle_id=cattle_id)
        return queryset


class MorphometricMeasurementViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = MorphometricMeasurementSerializer

    def get_queryset(self):
        queryset = MorphometricMeasurement.objects.filter(
            measurement__cattle__farm__in=accessible_farms(self.request.user),
            measurement__deleted_at__isnull=True,
            deleted_at__isnull=True,
        ).select_related("measurement", "measurement_type")
        measurement_id = uuid_query_param(self.request, "measurement")
        if measurement_id:
            queryset = queryset.filter(measurement_id=measurement_id)
        return queryset.order_by("measurement_type__name", "id")


class ScaleWeighingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ScaleWeighingSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("cattle__ear_tag",)
    ordering_fields = ("weighed_at", "created_at")
    ordering = ("-weighed_at", "-id")

    def get_queryset(self):
        queryset = ScaleWeighing.objects.filter(
            cattle__farm__in=accessible_farms(self.request.user), deleted_at__isnull=True
        ).select_related("cattle", "created_by")
        farm_id = uuid_query_param(self.request, "farm")
        cattle_id = uuid_query_param(self.request, "cattle")
        if farm_id:
            queryset = queryset.filter(cattle__farm_id=farm_id)
        if cattle_id:
            queryset = queryset.filter(cattle_id=cattle_id)
        return queryset
