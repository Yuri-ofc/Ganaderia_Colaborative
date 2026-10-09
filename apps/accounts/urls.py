from django.urls import path

from .views import LoginView, LogoutView, RegistrationView


urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
    path("token/", LoginView.as_view(), name="token"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
