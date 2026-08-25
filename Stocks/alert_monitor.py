import asyncio
import json
import websockets

from django.conf import settings
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer

from .services import (
    get_active_alerts,
    trigger_stock_alert,
    get_active_alert_symbols,
)

from .events import publish_stock_alert_triggered


# =========================================================
# PROCESS ONE LIVE STOCK PRICE
# =========================================================

async def process_stock_price(symbol, current_price):

    # Ask services.py for every active alert
    # that cares about this ticker.
    alerts = await sync_to_async(
        get_active_alerts
    )(symbol)

    triggered_any = False

    for alert in alerts:

        if alert.direction == "above":
            triggered = (
                current_price
                >= float(alert.target_price)
            )

        elif alert.direction == "below":
            triggered = (
                current_price
                <= float(alert.target_price)
            )

        else:
            continue

        if not triggered:
            continue

        # This specific alert was hit.
        result = await sync_to_async(
            trigger_stock_alert
        )(
            alert,
            current_price
        )

        if not result.get("success"):
            continue

        triggered_any = True

        # Tell the rest of the system that
        # this alert has now triggered.
        await sync_to_async(
            publish_stock_alert_triggered
        )(result)

    return triggered_any


# =========================================================
# REFRESH FINNHUB SUBSCRIPTIONS
# =========================================================

async def refresh_subscriptions(
    ws,
    subscribed_symbols,
    send_lock
):

    # Ask PostgreSQL which symbols currently
    # have at least one active alert.
    new_symbols = set(
        await sync_to_async(
            get_active_alert_symbols
        )()
    )

    # Compare database truth against what
    # Finnhub is currently streaming.
    added_symbols = (
        new_symbols
        - subscribed_symbols
    )

    removed_symbols = (
        subscribed_symbols
        - new_symbols
    )

    # Subscribe only to newly-needed symbols.
    for symbol in added_symbols:

        async with send_lock:
            await ws.send(
                json.dumps({
                    "type": "subscribe",
                    "symbol": symbol
                })
            )

        print(
            f"Alert monitor subscribed to {symbol}"
        )

    # Unsubscribe from symbols that no longer
    # have any active alerts.
    for symbol in removed_symbols:

        async with send_lock:
            await ws.send(
                json.dumps({
                    "type": "unsubscribe",
                    "symbol": symbol
                })
            )

        print(
            f"Alert monitor unsubscribed from {symbol}"
        )

    # Update our local representation so it
    # matches the database/Finnhub state.
    subscribed_symbols.clear()
    subscribed_symbols.update(
        new_symbols
    )


# =========================================================
# LISTEN TO FINNHUB
# =========================================================

async def listen_to_finnhub(
    ws,
    subscribed_symbols,
    send_lock
):

    while True:

        message = await ws.recv()

        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            continue

        if data.get("type") != "trade":
            continue

        for trade in data.get("data", []):

            symbol = trade.get("s")
            current_price = trade.get("p")

            if (
                not symbol
                or current_price is None
            ):
                continue

            # Compare this live price against
            # every active alert for the symbol.
            alert_triggered = (
                await process_stock_price(
                    symbol,
                    current_price
                )
            )

            # A triggered alert became inactive.
            #
            # If that was the final active alert
            # for this ticker, Finnhub no longer
            # needs to stream it.
            if alert_triggered:

                await refresh_subscriptions(
                    ws,
                    subscribed_symbols,
                    send_lock
                )


# =========================================================
# LISTEN TO REDIS / CHANNELS
# =========================================================

async def listen_for_subscription_changes(
    channel_layer,
    monitor_channel,
    ws,
    subscribed_symbols,
    send_lock
):

    while True:

        # Wait for an internal Channels event
        # sent to this monitor's channel.
        event = await channel_layer.receive(
            monitor_channel
        )

        if (
            event.get("type")
            != "alert_subscriptions_changed"
        ):
            continue

        print(
            "Alert subscriptions changed. "
            "Refreshing..."
        )

        # Something was created or removed.
        # Ask the DB for the current truth rather
        # than trusting the event to describe it.
        await refresh_subscriptions(
            ws,
            subscribed_symbols,
            send_lock
        )


# =========================================================
# MAIN ALERT MONITOR
# =========================================================

async def monitor_stock_alerts():

    socket_url = (
        f"wss://ws.finnhub.io"
        f"?token={settings.STOCKS_API_KEY}"
    )

    # This retrieves YOUR configured
    # Redis-backed Django Channels layer.
    channel_layer = get_channel_layer()

    # Create a private internal channel
    # representing this alert monitor process.
    monitor_channel = (
        await channel_layer.new_channel()
    )

    # Join that private channel to the
    # global alert-monitor group.
    await channel_layer.group_add(
        "stock_alert_monitor",
        monitor_channel
    )

    # Tracks what we've actually told Finnhub
    # to stream right now.
    subscribed_symbols = set()

    # Both async tasks can potentially send
    # subscribe/unsubscribe messages to the
    # same Finnhub WebSocket.
    send_lock = asyncio.Lock()

    try:

        async with websockets.connect(
            socket_url
        ) as ws:

            print(
                "Stock alert monitor connected "
                "to Finnhub."
            )

            # Initial subscription setup.
            await refresh_subscriptions(
                ws,
                subscribed_symbols,
                send_lock
            )

            # TASK 1:
            # continuously listen for market prices.
            finnhub_task = asyncio.create_task(
                listen_to_finnhub(
                    ws,
                    subscribed_symbols,
                    send_lock
                )
            )

            # TASK 2:
            # continuously listen for our backend
            # telling us alert configuration changed.
            subscription_task = (
                asyncio.create_task(
                    listen_for_subscription_changes(
                        channel_layer,
                        monitor_channel,
                        ws,
                        subscribed_symbols,
                        send_lock
                    )
                )
            )

            # Keep BOTH infinite listeners alive
            # concurrently.
            await asyncio.gather(
                finnhub_task,
                subscription_task
            )

    finally:

        # Clean up this monitor's membership
        # if the process shuts down.
        await channel_layer.group_discard(
            "stock_alert_monitor",
            monitor_channel
        )