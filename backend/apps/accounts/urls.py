from django.urls import path

from .views import (
    VistaBuscarUsuario,
    VistaCierreSesion,
    VistaInicioSesion,
    VistaPerfilUsuario,
    VistaRegistro,
)


urlpatterns = [
    path("register/", VistaRegistro.as_view(), name="register"),
    path("token/", VistaInicioSesion.as_view(), name="token"),
    path("me/", VistaPerfilUsuario.as_view(), name="me"),
    path("logout/", VistaCierreSesion.as_view(), name="logout"),
    path("buscar-usuario/", VistaBuscarUsuario.as_view(), name="buscar-usuario"),
]
