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

        # This will hold the active Finnhub WebSocket connection.
        self.finnhub_ws = None

        # Prevent two parts of the consumer from trying to send
        # to Finnhub at the exact same moment.
        self.finnhub_send_lock = asyncio.Lock()

        # Get this user's current stock preferences.
        self.symbols = await sync_to_async(
            get_user_symbols
        )(self.user)

        print(
            f"Subscribing to symbols for "
            f"{self.user if self.user.is_authenticated else 'Anonymous'}: "
            f"{self.symbols}"
        )

        # Authenticated users get their own Channels group.
        #
        # Later:
        # add_stock/remove_stock view
        #       ↓
        # group_send("stocks_user_5", ...)
        #       ↓
        # this consumer receives it
        if self.user.is_authenticated:
            self.group_name = f"stocks_user_{self.user.id}"

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

        else:
            self.group_name = None

        # Tell the browser which stock cards should currently exist.
        # This is useful even when the market is closed.
        await self.send(
            text_data=json.dumps({
                "type": "stock_preferences_changed",
                "symbols": self.symbols
            })
        )

        # Start the existing live Finnhub stream.
        self.task = asyncio.create_task(
            self.stream_stock_data()
        )


    async def disconnect(self, close_code):

        # Remove this WebSocket from the user's Channels group.
        if self.group_name is not None:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

        # Stop the Finnhub streaming task.
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

                # Save the Finnhub connection so another consumer method
                # can subscribe/unsubscribe symbols later.
                self.finnhub_ws = ws

                # Subscribe to the symbols that existed when the
                # mirror connected.
                for symbol in self.symbols:
                    await self.send_finnhub_command(
                        "subscribe",
                        symbol
                    )

                while True:
                    msg = await ws.recv()

                    # Preserve Finnhub's existing frontend contract.
                    # Trade messages still go straight to the mirror.
                    await self.send(
                        text_data=msg
                    )

        except asyncio.CancelledError:
            print("Stock WebSocket task cancelled.")
            raise

        except Exception as e:
            print(
                f"WebSocket error in stream_stock_data: {e}"
            )

        finally:
            self.finnhub_ws = None


    async def send_finnhub_command(self, command, symbol):
        """
        Sends subscribe/unsubscribe commands through the already-open
        Finnhub WebSocket.
        """

        if self.finnhub_ws is None:
            return

        async with self.finnhub_send_lock:
            await self.finnhub_ws.send(
                json.dumps({
                    "type": command,
                    "symbol": symbol
                })
            )


    async def stock_preferences_changed(self, event):
        """
        Called automatically by Django Channels when this user's
        stock preferences are changed by the remote or Jarvis.

        The database has already been updated by the time this runs.
        """

        new_symbols = await sync_to_async(
            get_user_symbols
        )(self.user)

        old_symbols = set(self.symbols)
        new_symbol_set = set(new_symbols)

        added_symbols = new_symbol_set - old_symbols
        removed_symbols = old_symbols - new_symbol_set

        # Subscribe newly-added stocks on the SAME Finnhub connection.
        for symbol in added_symbols:
            print(f"Adding live stock subscription: {symbol}")

            await self.send_finnhub_command(
                "subscribe",
                symbol
            )

        # Stop live updates for removed stocks.
        for symbol in removed_symbols:
            print(f"Removing live stock subscription: {symbol}")

            await self.send_finnhub_command(
                "unsubscribe",
                symbol
            )

        # Store the new preference list in the consumer.
        self.symbols = new_symbols

        # Tell the mirror frontend immediately which stock cards
        # should now exist.
        await self.send(
            text_data=json.dumps({
                "type": "stock_preferences_changed",
                "symbols": self.symbols
            })
        )