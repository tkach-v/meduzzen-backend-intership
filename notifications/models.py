from django.db import models
from enum import StrEnum, auto
from django.conf import settings

from common.models import TimeStampedModel


class NotificationStatuses(StrEnum):
    READ = auto()
    PENDING = auto()

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class Notification(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    status = models.CharField(choices=NotificationStatuses.choices(), default=NotificationStatuses.PENDING)

    class Meta:
        ordering = ['-created_at']
