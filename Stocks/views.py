from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests
from .models import StockPreference

@login_required
def stock_prices(request):
    API_KEY = settings.STOCKS_API_KEY  # Get Finnhub API key

    # Get the user's stock preferences
    stock_pref = StockPreference.objects.filter(user=request.user).first()

    if not stock_pref:
        return JsonResponse({"error": "No stock preferences set."}, status=400)

    # Collect stock symbols (ignore empty fields)
    stock_symbols = [
        stock_pref.stock_preference_one,
        stock_pref.stock_preference_two,
        stock_pref.stock_preference_three,
        stock_pref.stock_preference_four,
    ]
    stock_symbols = [symbol for symbol in stock_symbols if symbol]  # Remove None values

    stock_data = {}
    
    for symbol in stock_symbols:
        API_URL = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
        
        try:
            response = requests.get(API_URL)
            data = response.json()
            
            if "c" in data:  # 'c' is the current stock price
                stock_data[symbol] = {
                    "current_price": data["c"],
                    "high_price": data["h"],
                    "low_price": data["l"],
                    "open_price": data["o"],
                    "previous_close": data["pc"]
                }
            else:
                stock_data[symbol] = {"error": "Invalid stock symbol or data unavailable"}

        except requests.exceptions.RequestException:
            stock_data[symbol] = {"error": "Error connecting to stock API"}

    return JsonResponse({"stocks": stock_data})
