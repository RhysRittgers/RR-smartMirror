from .models import StockPreference, StockAlert
from django.utils import timezone


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

def create_stock_alert(user, symbol, target_price, direction):
    if not user.is_authenticated:
        return {
            "success": False,
            "error": "User is not authenticated"
        }
        
    symbol = symbol.strip().upper()
    direction = direction.strip().lower()
    
    try:
        target_price = float(target_price)
    except (TypeError, ValueError):
        return {
            "success": False,
            "error": "Target price must be a valid number"
        }
    
    if not symbol:
        return {
            "success": False,
            "error": "Stock symbol cannot be empty"
        }
    
    if target_price <= 0:
        return {
            "success": False,
            "error": "target price must be above 0"
        }
    
    if direction not in {"above", "below"}:
        return {
            "success": False,
            "error": "direction must be: above/below"
        }
        
    alert = StockAlert.objects.create(
        user=user,
        symbol=symbol,
        target_price=target_price,
        direction=direction
        
    )
    
    return {
        "success": True,
        "alert_id": alert.id,
        "user_id": user.id,
        "symbol": symbol,
        "target_price": target_price,
        "direction": direction
    }
    
def remove_stock_alert(user, alert_id):
    if not user.is_authenticated:
        return {
            "success": False,
            "error": "User is not authenticated"
        }
        
    if not alert_id:
        return {
            "success": False,
            "error": "Alert Id not found"
        }
        
    alert = StockAlert.objects.filter(
        user=user,
        id=alert_id
    ).first()
    
    if not alert:
        return {
            "success": False,
            "error": f"{alert_id} not found"
        }
    
    symbol = alert.symbol    
    alert.delete()
    
    return {
        "success": True,
        "alert_id": alert_id,
        "symbol": symbol,
        "user_id": user.id
    }
    
def get_active_alerts(symbol):
    symbol = symbol.strip().upper()
    
    active_alerts = StockAlert.objects.filter(
        symbol=symbol,
        active=True,
        triggered=False
        )
    
    return list(active_alerts)

def trigger_stock_alert(alert, current_price):
    if not alert.active or alert.triggered:
        return {
            "success": False,
            "error": "Alert is already inactive or triggered"
        }
    
    alert.active = False
    alert.triggered=True
    alert.triggered_at = timezone.now()
    alert.save()
    
    return {
        "success": True,
        "alert_id": alert.id,
        "user_id": alert.user.id,
        "symbol": alert.symbol,
        "target_price": float(alert.target_price),
        "current_price": current_price,
        "direction": alert.direction
    }
    
def get_user_alerts(user):
    return list(
        StockAlert.objects.filter(user=user)
    )
    
def get_active_alert_symbols():
    return list(
        StockAlert.objects
        .filter(
            active=True,
            triggered=False
        )
        .values_list("symbol", flat=True)
        .distinct()
    )
    
def get_stream_symbols():
    preference_symbols = set(
        StockPreference.objects
        .exclude(symbol="")
        .values_list("symbol", flat=True)
    )

    alert_symbols = set(
        StockAlert.objects
        .filter(
            active=True,
            triggered=False
        )
        .values_list("symbol", flat=True)
    )

    return list(
        preference_symbols | alert_symbols
    )