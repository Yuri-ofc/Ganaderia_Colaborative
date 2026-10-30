from django.conf import settings
from django.db import models


class Recurso(models.Model):
    """Permiso identificable por un código de cuatro caracteres del ERD."""

    idrecurso = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=4, unique=True)

    class Meta:
        db_table = "recurso"
        ordering = ("nombre",)

    def __str__(self):
        return self.nombre


class Rol(models.Model):
    """Rol global; sus permisos se expresan mediante ``rol_has_recurso``."""

    Rol_ID = models.AutoField(primary_key=True)
    Rol_nombre = models.CharField(max_length=4, unique=True)
    recursos = models.ManyToManyField(Recurso, through="RolHasRecurso", related_name="roles", blank=True)

    class Meta:
        db_table = "rol"
        ordering = ("Rol_nombre",)

    def __str__(self):
        return self.Rol_nombre


class UsuarioHasRol(models.Model):
    """Unión usuario--rol del diagrama. El usuario base conserva su UUID."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="Usuario_Usua_ID",
        related_name="asignaciones_rbac",
    )
    rol = models.ForeignKey(
        Rol,
        on_delete=models.CASCADE,
        db_column="Rol_Rol_ID",
        related_name="asignaciones_usuario",
    )
    pk = models.CompositePrimaryKey("usuario", "rol")

    class Meta:
        db_table = "usuario_has_rol"


class RolHasRecurso(models.Model):
    """Unión rol--recurso del diagrama."""

    rol = models.ForeignKey(
        Rol,
        on_delete=models.CASCADE,
        db_column="rol_Rol_ID",
        related_name="asignaciones_recurso",
    )
    recurso = models.ForeignKey(
        Recurso,
        on_delete=models.CASCADE,
        db_column="recurso_idrecurso",
        related_name="asignaciones_rol",
    )
    pk = models.CompositePrimaryKey("rol", "recurso")

    class Meta:
        db_table = "rol_has_recurso"
