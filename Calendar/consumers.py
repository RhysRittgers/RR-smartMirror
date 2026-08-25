from channels.generic.websocket import AsyncWebsocketConsumer
import json


class CalendarConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.group_name = "mirror_calendar"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        print("Calendar websocket connected")


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        print("Calendar websocket disconnected")


    async def calendar_event(self, event):
        await self.send(
            text_data=json.dumps({
                "event": event["event"]
            })
        )