from django.contrib import admin

from .models import Bovino, MovimientoPotrero, Potrero, Raza


@admin.register(Raza)
class AdminRaza(admin.ModelAdmin):
    list_display = ("nombre", "creado_en", "eliminado_en")
    search_fields = ("nombre",)


@admin.register(Potrero)
class AdminPotrero(admin.ModelAdmin):
    list_display = ("nombre", "finca", "creado_en", "eliminado_en")
    search_fields = ("nombre", "finca__nombre")
    list_select_related = ("finca",)


@admin.register(Bovino)
class AdminBovino(admin.ModelAdmin):
    list_display = ("arete", "finca", "potrero", "raza", "sexo", "estado_operativo", "eliminado_en")
    list_filter = ("sexo", "estado_operativo")
    search_fields = ("arete", "finca__nombre", "potrero__nombre", "raza__nombre")
    list_select_related = ("finca", "potrero", "raza")


@admin.register(MovimientoPotrero)
class AdminMovimientoPotrero(admin.ModelAdmin):
    list_display = ("bovino", "potrero", "iniciado_en", "finalizado_en")
    search_fields = ("bovino__arete", "potrero__nombre")
    list_select_related = ("bovino", "potrero")
