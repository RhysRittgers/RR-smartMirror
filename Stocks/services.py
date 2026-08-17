from .models import StockPreference


DEFAULT_SYMBOLS = ["AAPL", "TSLA"]


def get_user_symbols(user):
    if not user.is_authenticated:
        return DEFAULT_SYMBOLS.copy()

    symbols = list(
        StockPreference.objects
        .filter(user=user)
        .exclude(symbol="")
        .values_list("symbol", flat=True)
    )

    return symbols or DEFAULT_SYMBOLS.copy()


def seed_default_symbols(user):
    if StockPreference.objects.filter(user=user).exists():
        return

    for symbol in DEFAULT_SYMBOLS:
        StockPreference.objects.get_or_create(
            user=user,
            symbol=symbol
        )


def add_user_symbol(user, symbol):
    if not user.is_authenticated:
        return {
            "success": False,
            "error": "User is not authenticated"
        }

    symbol = symbol.strip().upper()

    if not symbol:
        return {
            "success": False,
            "error": "Stock symbol cannot be empty"
        }

    seed_default_symbols(user)

    stock, created = StockPreference.objects.get_or_create(
        user=user,
        symbol=symbol
    )

    if not created:
        return {
            "success": False,
            "error": f"{symbol} is already in your stocks"
        }

    return {
        "success": True,
        "symbol": symbol
    }


def remove_stock_symbol(user, symbol):
    if not user.is_authenticated:
        return {
            "success": False,
            "error": "User is not authenticated"
        }

    symbol = symbol.strip().upper()

    if not symbol:
        return {
            "success": False,
            "error": "Stock symbol cannot be empty"
        }

    seed_default_symbols(user)

    stock = StockPreference.objects.filter(
        user=user,
        symbol=symbol
    ).first()

    if not stock:
        return {
            "success": False,
            "error": f"{symbol} is not in your stocks"
        }

    stock.delete()

    return {
        "success": True,
        "symbol": symbol
    }

def create_stock_alert(user, symbol):
    if not user.is_authenticated:
        return {
            "success": False,
            "error": "User is not authenticated"
        }
        
def remove_stock_alert(user, symbol):
    if not user.is_authenticated:
        return {
            "success": False,
            "error": "User is not authenticated"
        }