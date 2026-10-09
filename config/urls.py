from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.backups.views import BackupViewSet
from apps.cattle.views import BreedViewSet, CattleViewSet, LotMovementViewSet, LotViewSet
from apps.farms.views import FarmViewSet, InvitationViewSet, MembershipViewSet
from apps.measurements.views import (
    AIModelViewSet,
    DeviceViewSet,
    MeasurementTypeViewSet,
    MeasurementViewSet,
    MorphometricMeasurementViewSet,
    ScaleWeighingViewSet,
)
from apps.sync.views import SyncChangeViewSet

router = DefaultRouter()
router.register("farms", FarmViewSet, basename="farm")
router.register("memberships", MembershipViewSet, basename="membership")
router.register("invitations", InvitationViewSet, basename="invitation")
router.register("breeds", BreedViewSet, basename="breed")
router.register("lots", LotViewSet, basename="lot")
router.register("cattle", CattleViewSet, basename="cattle")
router.register("lot-movements", LotMovementViewSet, basename="lot-movement")
router.register("devices", DeviceViewSet, basename="device")
router.register("ai-models", AIModelViewSet, basename="ai-model")
router.register("measurement-types", MeasurementTypeViewSet, basename="measurement-type")
router.register("measurements", MeasurementViewSet, basename="measurement")
router.register("morphometric-measurements", MorphometricMeasurementViewSet, basename="morphometric-measurement")
router.register("scale-weighings", ScaleWeighingViewSet, basename="scale-weighing")
router.register("backups", BackupViewSet, basename="backup")
router.register("sync-changes", SyncChangeViewSet, basename="sync-change")

urlpatterns = [
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include(router.urls)),
]
