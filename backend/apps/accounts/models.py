from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.models import ModeloBaseUuid


class Usuario(ModeloBaseUuid, AbstractUser):
    telefono = models.CharField(max_length=20, null=True, blank=True)
    hash_frase_recuperacion = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("telefono",),
                condition=models.Q(telefono__isnull=False, eliminado_en__isnull=True),
                name="telefono_usuario_activo_unico",
            ),
        ]

    def __str__(self):
        return self.username
