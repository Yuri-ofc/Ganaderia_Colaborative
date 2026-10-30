from django.contrib import admin

from .models import Recurso, Rol


@admin.register(Rol)
class AdminRol(admin.ModelAdmin):
    list_display = ("Rol_ID", "Rol_nombre")
    search_fields = ("Rol_nombre",)


admin.site.register(Recurso)
