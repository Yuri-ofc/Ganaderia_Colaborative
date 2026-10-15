from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class AdminUsuario(UserAdmin):
    list_display = ("username", "email", "telefono", "is_staff", "is_active", "eliminado_en")
    list_filter = ("is_staff", "is_active")
    search_fields = ("username", "email", "telefono")
    ordering = ("username",)
    readonly_fields = ("id", "creado_en", "actualizado_en")
    fieldsets = UserAdmin.fieldsets + (
        ("Datos del proyecto", {"fields": ("telefono", "hash_frase_recuperacion", "eliminado_en")}),
        ("Trazabilidad", {"fields": ("id", "creado_en", "actualizado_en")}),
    )
