from channels.generic.websocket import AsyncJsonWebsocketConsumer

class SpotifyConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close()
            return
        self.group = f"user_{user.id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def spotify_update(self, event):
        await self.send_json({"type": "spotify_state", "data": event["payload"]})
