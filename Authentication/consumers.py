# Authentication/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
import json
import aiohttp

class MirrorLoginConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "mirror_login"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get("type") == "send_token_to_mirror":
            token = data.get("token")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://mirror.rr-smartmirror.com/auth/mirror-auth/",
                    data={"token": token}
                ) as resp:
                    if resp.status == 200:
                        await self.channel_layer.group_send(
                            self.group_name,
                            {"type": "login_success", "username": "authed", "token": token}
                        )
                    else:
                        await self.send(text_data=json.dumps({"type": "login_failed"}))

    async def login_success(self, event):
        await self.send(text_data=json.dumps({
            "type": "login_success",
            "username": event["username"],
            "token": event.get("token")
        }))

class SettingsConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close()
            return
        await self.channel_layer.group_add("mirror_settings", self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard("mirror_settings", self.channel_name)

    # receives {"type": "time_pref", "use_24h": ...}
    async def time_pref(self, event):
        await self.send_json({"type": "time_pref", "use_24h": bool(event.get("use_24h"))})
