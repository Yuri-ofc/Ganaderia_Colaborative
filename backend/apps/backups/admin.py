from django.contrib import admin

from .models import Respaldo


@admin.register(Respaldo)
class AdminRespaldo(admin.ModelAdmin):
    list_display = ("finca", "version", "tamano_bytes", "cifrado", "creado_en")
    list_filter = ("cifrado",)
    search_fields = ("finca__nombre", "version", "suma_verificacion")
    list_select_related = ("finca", "creado_por")
