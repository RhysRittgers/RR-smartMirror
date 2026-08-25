import asyncio
import json
import websockets

from django.conf import settings
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer

from .services import (
    get_active_alerts,
    trigger_stock_alert,
    get_stream_symbols,
)

from .events import (
    publish_stock_alert_triggered,
    publish_stock_price_update,
)


# =========================================================
# PROCESS ONE LIVE STOCK PRICE
# =========================================================

async def process_stock_price(symbol, current_price):

    # Find every active alert interested in this symbol.
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

        # Persist the triggered state in PostgreSQL.
        result = await sync_to_async(
            trigger_stock_alert
        )(
            alert,
            current_price
        )

        if not result.get("success"):
            continue

        triggered_any = True

        # Publish the triggered alert through Redis/Channels.
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

    # IMPORTANT:
    # Finnhub must stream symbols needed for BOTH:
    #
    # 1. live mirror stock displays
    # 2. active stock alerts
    #
    # get_stream_symbols() returns the union of both.
    new_symbols = set(
        await sync_to_async(
            get_stream_symbols
        )()
    )

    added_symbols = (
        new_symbols
        - subscribed_symbols
    )

    removed_symbols = (
        subscribed_symbols
        - new_symbols
    )

    for symbol in added_symbols:

        async with send_lock:
            await ws.send(
                json.dumps({
                    "type": "subscribe",
                    "symbol": symbol
                })
            )

        print(
            f"Stock worker subscribed to {symbol}",
            flush=True
        )

    for symbol in removed_symbols:

        async with send_lock:
            await ws.send(
                json.dumps({
                    "type": "unsubscribe",
                    "symbol": symbol
                })
            )

        print(
            f"Stock worker unsubscribed from {symbol}",
            flush=True
        )

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

            # -------------------------------------------------
            # JOB 1:
            # Publish every live price into Redis.
            #
            # StocksConsumer receives this and forwards it to
            # mirrors that actually display this symbol.
            # -------------------------------------------------

            await sync_to_async(
                publish_stock_price_update
            )(
                symbol,
                current_price
            )

            # -------------------------------------------------
            # JOB 2:
            # Check the same price against active alerts.
            # -------------------------------------------------

            alert_triggered = (
                await process_stock_price(
                    symbol,
                    current_price
                )
            )

            # An alert may have just become inactive.
            # Recalculate subscriptions in case this symbol
            # is no longer needed by either displays or alerts.
            if alert_triggered:

                await refresh_subscriptions(
                    ws,
                    subscribed_symbols,
                    send_lock
                )


# =========================================================
# LISTEN FOR INTERNAL SUBSCRIPTION CHANGES
# =========================================================

async def listen_for_subscription_changes(
    channel_layer,
    monitor_channel,
    ws,
    subscribed_symbols,
    send_lock
):

    while True:

        event = await channel_layer.receive(
            monitor_channel
        )

        if (
            event.get("type")
            != "alert_subscriptions_changed"
        ):
            continue

        print(
            "Stock subscriptions changed. Refreshing...",
            flush=True
        )

        await refresh_subscriptions(
            ws,
            subscribed_symbols,
            send_lock
        )


# =========================================================
# RUN ONE FINNHUB CONNECTION
# =========================================================

async def run_finnhub_connection(
    channel_layer,
    monitor_channel
):

    socket_url = (
        f"wss://ws.finnhub.io"
        f"?token={settings.STOCKS_API_KEY}"
    )

    subscribed_symbols = set()
    send_lock = asyncio.Lock()

    async with websockets.connect(
        socket_url
    ) as ws:

        print(
            "Stock alert monitor connected to Finnhub.",
            flush=True
        )

        await refresh_subscriptions(
            ws,
            subscribed_symbols,
            send_lock
        )

        finnhub_task = asyncio.create_task(
            listen_to_finnhub(
                ws,
                subscribed_symbols,
                send_lock
            )
        )

        subscription_task = asyncio.create_task(
            listen_for_subscription_changes(
                channel_layer,
                monitor_channel,
                ws,
                subscribed_symbols,
                send_lock
            )
        )

        try:
            # If either task dies, stop this connection
            # so the outer monitor can reconnect cleanly.
            done, pending = await asyncio.wait(
                {
                    finnhub_task,
                    subscription_task
                },
                return_when=asyncio.FIRST_EXCEPTION
            )

            for task in done:
                exception = task.exception()

                if exception:
                    raise exception

        finally:

            finnhub_task.cancel()
            subscription_task.cancel()

            await asyncio.gather(
                finnhub_task,
                subscription_task,
                return_exceptions=True
            )


# =========================================================
# MAIN STOCK WORKER
# =========================================================

async def monitor_stock_alerts():

    channel_layer = get_channel_layer()

    # Private internal Redis/Channels channel representing
    # this continuously-running background worker.
    monitor_channel = (
        await channel_layer.new_channel()
    )

    await channel_layer.group_add(
        "stock_alert_monitor",
        monitor_channel
    )

    try:

        # The worker should never permanently die simply
        # because Finnhub temporarily drops the WebSocket.
        while True:

            try:

                await run_finnhub_connection(
                    channel_layer,
                    monitor_channel
                )

            except asyncio.CancelledError:
                raise

            except Exception as exc:

                print(
                    f"Finnhub connection lost: {exc}",
                    flush=True
                )

                print(
                    "Reconnecting to Finnhub in 5 seconds...",
                    flush=True
                )

                await asyncio.sleep(5)

    finally:

        await channel_layer.group_discard(
            "stock_alert_monitor",
            monitor_channel
        )