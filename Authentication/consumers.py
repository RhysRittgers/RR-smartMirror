# Authentication/mirror_login_consumer.py

from channels.generic.websocket import AsyncWebsocketConsumer
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

        #token login only
        if data.get("type") == "send_token_to_mirror":
            token = data.get("token")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://mirror.rr-smartmirror.com/auth/mirror-auth/",
                    data={"token": token}
                ) as resp:
                    if resp.status == 200:
                        print("Mirror authenticated successfully.")
                        await self.channel_layer.group_send(
                            self.group_name,
                            {
                                "type": "login_success",
                                "username": "authed",
                                "token": token
                            }
                        )
                    else:
                        print(f"Mirror login failed. Status: {resp.status}")
                        await self.send(text_data=json.dumps({
                            "type": "login_failed"
                        }))

    #called when group_send sends { "type": "login_success" 
    async def login_success(self, event):
        await self.send(text_data=json.dumps({
            "type": "login_success",
            "username": event['username'],
            "token": event.get("token")
        }))
