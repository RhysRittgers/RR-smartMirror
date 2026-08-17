from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings

import requests

from .services import get_user_symbols


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