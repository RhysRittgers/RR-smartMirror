import json

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from .services import get_user_symbols


class StocksConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()

        self.user = self.scope.get("user")

        self.symbols = await sync_to_async(
            get_user_symbols
        )(self.user)

        print(
            f"Stock display connected for "
            f"{self.user if self.user.is_authenticated else 'Anonymous'}: "
            f"{self.symbols}"
        )

        # User-specific group:
        # preferences and triggered alerts.
        if self.user.is_authenticated:
            self.group_name = (
                f"stocks_user_{self.user.id}"
            )

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
        else:
            self.group_name = None

        # Global live-price group.
        #
        # The background worker owns the ONE Finnhub connection
        # and publishes prices here. Each consumer filters those
        # events against its own selected symbols.
        self.live_prices_group = "stocks_live_prices"

        await self.channel_layer.group_add(
            self.live_prices_group,
            self.channel_name
        )

        # Tell frontend which cards should exist.
        await self.send(
            text_data=json.dumps({
                "type": "stock_preferences_changed",
                "symbols": self.symbols
            })
        )


    async def disconnect(self, close_code):

        if self.group_name is not None:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

        await self.channel_layer.group_discard(
            self.live_prices_group,
            self.channel_name
        )


    async def stock_preferences_changed(self, event):

        self.symbols = await sync_to_async(
            get_user_symbols
        )(self.user)

        await self.send(
            text_data=json.dumps({
                "type": "stock_preferences_changed",
                "symbols": self.symbols
            })
        )


    async def stock_price_update(self, event):
        """
        Receive a live price from the background worker.

        The global Redis group receives prices for every ticker
        being monitored, but this mirror only forwards symbols
        that belong to this user's preferences.
        """

        symbol = event["symbol"]

        if symbol not in self.symbols:
            return

        # Preserve the Finnhub-style frontend contract so
        # index.html does not need to be rewritten.
        await self.send(
            text_data=json.dumps({
                "type": "trade",
                "data": [
                    {
                        "s": symbol,
                        "p": event["current_price"]
                    }
                ]
            })
        )
        
    async def stock_alert_created(self, event):

        await self.send(
            text_data=json.dumps({
                "type": "stock_alert_created",
                "event_type": event["event_type"],
                "alert_id": event["alert_id"],
                "symbol": event["symbol"],
                "target_price": event["target_price"],
                "direction": event["direction"],
            })
        )


    async def stock_alert_triggered(self, event):

        await self.send(
            text_data=json.dumps({
                "type": "stock_alert_triggered",
                "event_type": event["event_type"],
                "alert_id": event["alert_id"],
                "symbol": event["symbol"],
                "target_price": event["target_price"],
                "current_price": event["current_price"],
                "direction": event["direction"],
            })
        )
    
    async def stock_alert_removed(self, event):
        
        await self.send(text_data=json.dumps({
            "type": "stock_alert_removed",
            "event_type": event["event_type"],
            "alert_id": event["alert_id"],
            "symbol": event["symbol"],
        }))