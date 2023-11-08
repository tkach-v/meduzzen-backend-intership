import json

from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            self.close()
        else:
            self.group_name = str(self.scope["user"].pk)
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def notify(self, event):
        message = event['message']
        await self.send(text_data=json.dumps(message))
