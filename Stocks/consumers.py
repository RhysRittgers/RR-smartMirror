import json
import asyncio
import websockets

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.conf import settings

from .services import get_user_symbols


class StocksConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()

        self.user = self.scope.get("user")

        # Shared stock preference logic
        self.symbols = await sync_to_async(get_user_symbols)(self.user)

        print(
            f"Subscribing to symbols for "
            f"{self.user if self.user.is_authenticated else 'Anonymous'}: "
            f"{self.symbols}"
        )

        self.task = asyncio.create_task(
            self.stream_stock_data()
        )


    async def disconnect(self, close_code):
        if hasattr(self, "task"):
            self.task.cancel()


    async def stream_stock_data(self):
        print("stream_stock_data() started")

        socket_url = (
            f"wss://ws.finnhub.io"
            f"?token={settings.STOCKS_API_KEY}"
        )

        try:
            async with websockets.connect(socket_url) as ws:

                for symbol in self.symbols:
                    await ws.send(
                        json.dumps({
                            "type": "subscribe",
                            "symbol": symbol
                        })
                    )

                while True:
                    msg = await ws.recv()

                    # Preserve current frontend contract exactly.
                    await self.send(msg)

        except asyncio.CancelledError:
            print("Stock WebSocket task cancelled.")
            raise

        except Exception as e:
            print(
                f"WebSocket error in stream_stock_data: {e}"
            )