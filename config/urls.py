"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
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
    path('admin/', admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include(router.urls)),
]
