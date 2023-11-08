from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import Notification
from notifications.send_notification import send_notification


@receiver(post_save, sender=Notification)
def notification_handler(sender, instance, created, **kwargs):
    if created:
        send_notification(instance)
