# spotify/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class SpotifyConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close()
            return

        # Keep user group (future per-user isolation), and also a shared mirror group.
        self.user_group = f"user_{user.id}"
        self.shared_group = "mirror_spotify"

        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.channel_layer.group_add(self.shared_group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "user_group"):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        if hasattr(self, "shared_group"):
            await self.channel_layer.group_discard(self.shared_group, self.channel_name)

    # Called when the channel layer receives {"type": "spotify.update", "payload": ...}
    async def spotify_update(self, event):
        await self.send_json({"type": "spotify_state", "data": event.get("payload")})
