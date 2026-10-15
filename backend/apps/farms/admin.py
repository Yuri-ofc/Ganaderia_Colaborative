from django.contrib import admin

from .models import Finca, Invitacion, Membresia


@admin.register(Finca)
class AdminFinca(admin.ModelAdmin):
    list_display = ("nombre", "propietario", "ubicacion", "creado_en", "eliminado_en")
    search_fields = ("nombre", "ubicacion", "propietario__username")
    list_select_related = ("propietario",)


@admin.register(Membresia)
class AdminMembresia(admin.ModelAdmin):
    list_display = ("finca", "usuario", "rol", "invitado_por", "creado_en", "eliminado_en")
    list_filter = ("rol",)
    search_fields = ("finca__nombre", "usuario__username")
    list_select_related = ("finca", "usuario", "invitado_por")


@admin.register(Invitacion)
class AdminInvitacion(admin.ModelAdmin):
    list_display = ("finca", "telefono", "rol", "estado", "expira_en", "aceptado_en")
    list_filter = ("estado", "rol")
    search_fields = ("finca__nombre", "telefono")
    list_select_related = ("finca",)
