from rest_framework.routers import SimpleRouter

from .views import VistaFincas, VistaInvitaciones, VistaMembresias

router = SimpleRouter()
router.register("farms", VistaFincas, basename="farm")
router.register("memberships", VistaMembresias, basename="membership")
router.register("invitations", VistaInvitaciones, basename="invitation")

urlpatterns = router.urls
