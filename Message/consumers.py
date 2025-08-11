from channels.generic.websocket import AsyncWebsocketConsumer
import json
from Message.models import CustomMessage

class MirrorConsumer(AsyncWebsocketConsumer):

    @staticmethod
    async def get_user_message(user):
        try:
            message_obj = await CustomMessage.objects.filter(user=user).afirst()
            return message_obj.custom_message if message_obj else "No custom message set."
        except:
            return "Error loading message"

    async def connect(self):
        self.group_name = "mirror_display"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        user = self.scope["user"]
        if user.is_authenticated:
            message = await self.get_user_message(user)
        else:
            message = "Welcome"

        await self.send(text_data=json.dumps({
            "message": message
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print('Connection closed')

    async def broadcast_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({
            "message": message
        }))

    # New method: handle message from remote
    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("type") == "broadcast_message":
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "broadcast_message",
                    "message": data["message"]
                }
            )
