from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from pydantic import BaseModel

from notifications.models import Notification


class NotificationData(BaseModel):
    type: str
    message: str


def send_notification(notification: Notification) -> None:
    channel_layer = get_channel_layer()
    user_group_name = str(notification.user.id)
    notification_data = NotificationData(type='notify', message=notification.text).model_dump()
    async_to_sync(channel_layer.group_send)(
        user_group_name,
        notification_data
    )
