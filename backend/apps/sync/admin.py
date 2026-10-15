from django.contrib import admin

from .models import CambioSincronizacion


@admin.register(CambioSincronizacion)
class AdminCambioSincronizacion(admin.ModelAdmin):
    list_display = ("finca", "dispositivo", "recurso", "accion", "creado_en", "sincronizado_en")
    list_filter = ("accion", "recurso")
    search_fields = ("finca__nombre", "recurso", "id_objeto")
    list_select_related = ("finca", "dispositivo", "creado_por")
