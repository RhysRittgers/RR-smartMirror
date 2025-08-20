import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.sessions import SessionMiddlewareStack

# ✅ Set settings module BEFORE loading Django/URLs
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_mirror_project.settings")

# Create the Django ASGI app first
django_asgi_app = get_asgi_application()

# Import WS routes AFTER settings are loaded
from Stocks.routing import websocket_urlpatterns as stocks_ws
from Message.routing import websocket_urlpatterns as message_ws
from Calendar.routing import websocket_urlpatterns as calendar_ws
from Authentication.routing import websocket_urlpatterns as auth_ws
from spotify.routing import websocket_urlpatterns as spotify_ws  # ✅ NEW

combined_websockets = stocks_ws + message_ws + calendar_ws + auth_ws + spotify_ws  # ✅ add spotify

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": SessionMiddlewareStack(   # keep your wrapper
        AuthMiddlewareStack(
            URLRouter(combined_websockets)
        )
    ),
})
