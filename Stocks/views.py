from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json
import requests
from .services import add_user_symbol, get_user_symbols, remove_stock_symbol, create_stock_alert, remove_stock_alert
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def broadcast_stock_preference_change(user):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"stocks_user_{user.id}",
        {
            "type": "stock_preferences_changed"
        }
    )

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
        
    return JsonResponse(result)

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
    
    return JsonResponse(result)

def create_alert(request):
    pass

def remove_alert(request):
    pass