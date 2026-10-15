from django.urls import path

from .views import VistaCierreSesion, VistaInicioSesion, VistaRegistro


urlpatterns = [
    path("register/", VistaRegistro.as_view(), name="register"),
    path("token/", VistaInicioSesion.as_view(), name="token"),
    path("logout/", VistaCierreSesion.as_view(), name="logout"),
]
