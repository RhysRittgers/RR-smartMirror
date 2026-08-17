from .models import StockPreference


DEFAULT_SYMBOLS = ["AAPL", "TSLA"]


def get_user_symbols(user):
    if not user.is_authenticated:
        return DEFAULT_SYMBOLS

    symbols = list(
        StockPreference.objects
        .filter(user=user)
        .exclude(symbol="")
        .values_list("symbol", flat=True)
    )

    return symbols or DEFAULT_SYMBOLS.copy()