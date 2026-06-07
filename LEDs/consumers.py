from channels.generic.websocket import AsyncJsonWebsocketConsumer


class LEDConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.group_name = "led_commands"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def led_command(self, event):
        await self.send_json({
            "type": "led_command",
            "command": event.get("command"),
            "payload": event.get("payload", {})
        })