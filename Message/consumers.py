from channels.generic.websocket import AsyncWebsocketConsumer
import json
from Message.models import CustomMessage


class MirrorConsumer(AsyncWebsocketConsumer):
    @staticmethod
    async def get_user_message(user):
        try:
            message_obj = await CustomMessage.objects.filter(user=user).afirst()
            return message_obj.custom_message if message_obj else "No custom message set."
        except Exception:
            return "Error loading message"

    async def connect(self):
        self.group_name = "mirror_display"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        user = self.scope.get("user")
        if user and user.is_authenticated:
            message = await self.get_user_message(user)
        else:
            message = "Welcome"

        await self.send(text_data=json.dumps({
            "message": message
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print("Connection closed")

    async def broadcast_message(self, event):
        """
        Handler for group_send events with type="broadcast_message".
        """
        message = event.get("message", "")
        await self.send(text_data=json.dumps({
            "message": message
        }))

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle messages coming *from* any client connected to /ws/mirror.
        We use this so the remote dashboard can trigger broadcasts too.
        """
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")

        # Allow remote dashboard (or any client) to trigger a broadcast
        if msg_type == "broadcast_message":
            message = data.get("message", "")
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "broadcast_message",
                    "message": message
                }
            )
