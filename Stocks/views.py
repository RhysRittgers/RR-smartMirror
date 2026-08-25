from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json
import requests
from .services import add_user_symbol, get_user_symbols, remove_stock_symbol, create_stock_alert, remove_stock_alert, get_user_alerts
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt
from .events import publish_alert_subscriptions_changed

def broadcast_stock_preference_change(user):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"stocks_user_{user.id}",
        {
            "type": "stock_preferences_changed"
        }
    )
@csrf_exempt
@login_required
def stock_prices(request):

    stock_symbols = get_user_symbols(request.user)

    stock_data = {}

    for symbol in stock_symbols:

        api_url = (
            f"https://finnhub.io/api/v1/quote"
            f"?symbol={symbol}"
            f"&token={settings.STOCKS_API_KEY}"
        )

        try:
            response = requests.get(
                api_url,
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

        except requests.RequestException:
            stock_data[symbol] = {
                "error": "Error connecting to stock API"
            }
            continue

        except ValueError:
            stock_data[symbol] = {
                "error": "Stock API returned invalid JSON"
            }
            continue

        if "c" in data:
            stock_data[symbol] = {
                "current_price": data["c"],
                "high_price": data["h"],
                "low_price": data["l"],
                "open_price": data["o"],
                "previous_close": data["pc"],
            }

        else:
            stock_data[symbol] = {
                "error": "Invalid stock symbol or data unavailable"
            }

    return JsonResponse({
        "stocks": stock_data
    })

@csrf_exempt
@login_required    
def add_stock(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
    try:
        data = json.loads(request.body)
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    symbol = data.get("symbol")

    if symbol is None:
        return JsonResponse(
        {"error": "Must provide stock ticker"},
        status=400
    )

    if not isinstance(symbol, str):
        return JsonResponse(
            {"error": "Ticker must be a string"},
            status=422
        )

    symbol = symbol.strip()

    if not symbol:
        return JsonResponse(
            {"error": "Ticker cannot be empty"},
            status=400
        )

    if len(symbol) > 10:
        return JsonResponse(
            {"error": "Ticker exceeds maximum length"},
            status=422
        )
        
    result = add_user_symbol(
        request.user,
        symbol
    )
    
    if result.get("success"):
        broadcast_stock_preference_change(request.user)
        publish_alert_subscriptions_changed()
        
    return JsonResponse(result)

@csrf_exempt
@login_required
def remove_stock(request):
    if request.method != "DELETE":
        return JsonResponse(
            {"error": "Invalid request method"},
            status=405
        )
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400
        )
        
    symbol = data.get("symbol")
    
    if symbol is None:
        return JsonResponse(
            {"error": "Must provide stock ticker"},
            status=400
        )

    if not isinstance(symbol, str):
        return JsonResponse(
            {"error": "Ticker must be a string"},
            status=422
        )

    symbol = symbol.strip()

    if not symbol:
        return JsonResponse(
            {"error": "Ticker cannot be empty"},
            status=400
        )
    
    result = remove_stock_symbol(
        request.user,
        symbol
    )
    
    if result.get("success"):
        broadcast_stock_preference_change(request.user)
        publish_alert_subscriptions_changed()
    
    return JsonResponse(result)

@csrf_exempt
@login_required
def create_alert(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "bad request"}, status=400)
    
    symbol = data.get("symbol")
    target_price = data.get("target_price")
    direction = data.get("direction")
    
    if symbol is None:
        return JsonResponse(
        {"error": "Must provide stock ticker"},
        status=400
    )
    if target_price is None:
        return JsonResponse(
        {"error": "Must provide target price"},
        status=400
    )
    if direction is None:
        return JsonResponse(
        {"error": "Must provide direction"},
        status=400
    )
    
    if not isinstance(symbol, str):
        return JsonResponse({"error": "symbol must be a string"}, status=400)
    if not isinstance(direction, str):
        return JsonResponse(
            {"error": "Direction must be a string"},
            status=400
        )
    if direction.strip().lower() not in ["above", "below"]:
        return JsonResponse({"error": "direction must be: above or below"})
    
    symbol = symbol.strip()
    
    if not symbol:
        return JsonResponse(
            {"error": "Ticker cannot be empty"},
            status=400
        )

    direction = direction.strip()
    
    if not direction:
        return JsonResponse(
            {"error": "direction cannot be empty"}, 
            status=400
        )
    
    result = create_stock_alert(
        request.user,
        symbol,target_price,
        direction
    )
    
    if not result.get("success"):
        return JsonResponse(result, status=400)

    publish_alert_subscriptions_changed()

    return JsonResponse(result, status=201)

@csrf_exempt
@login_required
def remove_alert(request):
    if request.method != "DELETE":
        return JsonResponse(
            {"error": "Invalid request method"},
            status=405
        )
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid Json"},
            status=400
        )
        
    alert_id = data.get("alert_id")
    
    if alert_id is None:
        return JsonResponse(
            {"error": "Must provide alert id"},
            status=400
        )
    
    if not isinstance(alert_id, int):
        return JsonResponse(
            {"error": "ID must be an integer"},
            status=400
        )
    
    result = remove_stock_alert(
        user=request.user,
        alert_id=alert_id
    )
    
    if not result.get("success"):
        return JsonResponse(result, status=400)
    
    publish_alert_subscriptions_changed()
    
    return JsonResponse(result)

@login_required
def stock_alerts(request):
    alerts = get_user_alerts(request.user)
    
    alert_data = []
    for alert in alerts:
        alert_data.append({
            "alert_id": alert.id,
            "symbol": alert.symbol,
            "target_price": float(alert.target_price),
            "direction": alert.direction,
            "active": alert.active,
            "triggered": alert.triggered,
            "triggered_at": (
                alert.triggered_at.isoformat()
                if alert.triggered_at
                else None
            )
        })
    return JsonResponse({
        "alerts": alert_data
    })