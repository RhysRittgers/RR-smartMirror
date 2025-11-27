from channels.generic.websocket import AsyncWebsocketConsumer
import json


class CalendarConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "mirror_calendar"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print("Calendar websocket connected")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print("Calendar websocket disconnected")

    async def calendar_event(self, event):
        """
        Called when someone does:
        channel_layer.group_send("mirror_calendar", {"type": "calendar_event", "event": {...}})
        """
        await self.send(text_data=json.dumps({
            "event": event["event"]
        }))

    async def receive(self, text_data=None, bytes_data=None):
        """
        Allows any client (like the remote dashboard) to push a new event
        into the "mirror_calendar" group in real time.
        """
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if data.get("type") == "calendar_event":
            event_payload = data.get("event", {})
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "calendar_event",
                    "event": event_payload
                }
            )
