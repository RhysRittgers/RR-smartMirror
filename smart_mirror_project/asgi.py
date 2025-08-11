import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.sessions import SessionMiddlewareStack  # ✅ Add this

django.setup()

from Stocks.routing import websocket_urlpatterns as stocks_ws
from Message.routing import websocket_urlpatterns as message_ws
from Calendar.routing import websocket_urlpatterns as calendar_ws
from Authentication.routing import websocket_urlpatterns as auth_ws

combined_websockets = stocks_ws + message_ws + calendar_ws + auth_ws

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_mirror_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": SessionMiddlewareStack(  # ✅ Wrap this around
        AuthMiddlewareStack(
            URLRouter(combined_websockets)
        )
    ),
})
