import json
from enum import StrEnum, auto

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

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


@receiver(post_save, sender=Notification)
def notification_handler(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        user_group_name = str(instance.user.id)
        async_to_sync(channel_layer.group_send)(
            user_group_name,
            {
                'type': 'notify',
                'message': json.dumps(instance.text)
            }
        )
