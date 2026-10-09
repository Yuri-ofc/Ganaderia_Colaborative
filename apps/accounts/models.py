from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.models import UUIDTimeStampedModel


class User(UUIDTimeStampedModel, AbstractUser):
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    recovery_phrase_hash = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("phone_number",),
                condition=models.Q(phone_number__isnull=False, deleted_at__isnull=True),
                name="unique_active_user_phone",
            ),
        ]

    def __str__(self):
        return self.username
