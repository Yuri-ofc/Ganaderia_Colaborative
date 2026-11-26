from django.contrib import admin

from .models import CapturaVision


@admin.register(CapturaVision)
class AdminCapturaVision(admin.ModelAdmin):
    list_display = ("bovino", "tipo_archivo", "medicion", "creado_en")
    list_filter = ("tipo_archivo",)
    search_fields = ("bovino__arete",)
    list_select_related = ("bovino", "creado_por", "medicion")
