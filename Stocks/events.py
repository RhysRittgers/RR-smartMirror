from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def publish_stock_alert_triggered(result):
    channel_layer = get_channel_layer()

    user_id = result["user_id"]

    event = {
        "type": "stock_alert_triggered",
        "event_type": "stock.alert.triggered",
        "alert_id": result["alert_id"],
        "user_id": user_id,
        "symbol": result["symbol"],
        "target_price": result["target_price"],
        "current_price": result["current_price"],
        "direction": result["direction"],
    }

    async_to_sync(channel_layer.group_send)(
        f"stocks_user_{user_id}",
        event
    )
    
def publish_alert_subscriptions_changed():
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "stock_alert_monitor",
        {
            "type": "alert_subscriptions_changed"
        }
    )
    
def publish_stock_price_update(symbol, current_price):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "stocks_live_prices",
        {
            "type": "stock_price_update",
            "symbol": symbol,
            "current_price": current_price,
        }
    )