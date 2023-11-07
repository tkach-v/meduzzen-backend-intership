import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from notifications.models import Notification


def send_notification(notification: Notification) -> None:
    channel_layer = get_channel_layer()
    user_group_name = str(notification.user.id)
    async_to_sync(channel_layer.group_send)(
        user_group_name,
        {
            'type': 'notify',
            'message': json.dumps(notification.text)
        }
    )
