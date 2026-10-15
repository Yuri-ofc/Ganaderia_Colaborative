from django.contrib import admin

from .models import Dispositivo, Medicion, MedidaMorfometrica, ModeloIa, Pesaje, TipoMedida


@admin.register(Dispositivo)
class AdminDispositivo(admin.ModelAdmin):
    list_display = ("modelo", "propietario", "sistema_operativo", "ultima_conexion_en")
    search_fields = ("modelo", "propietario__username")
    list_select_related = ("propietario",)


@admin.register(ModeloIa)
class AdminModeloIa(admin.ModelAdmin):
    list_display = ("version", "calibracion", "activo", "creado_en")
    list_filter = ("activo",)
    search_fields = ("version",)


@admin.register(TipoMedida)
class AdminTipoMedida(admin.ModelAdmin):
    list_display = ("nombre", "unidad")
    search_fields = ("nombre",)


@admin.register(Medicion)
class AdminMedicion(admin.ModelAdmin):
    list_display = ("bovino", "capturado_en", "modo_captura", "peso_estimado_kg", "nivel_confianza")
    list_filter = ("modo_captura",)
    search_fields = ("bovino__arete",)
    list_select_related = ("bovino", "dispositivo", "modelo_ia")
    readonly_fields = [campo.name for campo in Medicion._meta.fields]

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(MedidaMorfometrica)
class AdminMedidaMorfometrica(admin.ModelAdmin):
    list_display = ("medicion", "tipo_medida", "valor")
    list_select_related = ("medicion", "tipo_medida")
    readonly_fields = [campo.name for campo in MedidaMorfometrica._meta.fields]

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Pesaje)
class AdminPesaje(admin.ModelAdmin):
    list_display = ("bovino", "pesado_en", "tipo_bascula", "peso_real_kg")
    search_fields = ("bovino__arete",)
    list_select_related = ("bovino", "creado_por")
    readonly_fields = [campo.name for campo in Pesaje._meta.fields]

    def has_change_permission(self, request, obj=None):
        return False
