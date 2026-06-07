from django.urls import path
from .consumers import LEDConsumer

websocket_urlpatterns = [
    path("ws/leds/", LEDConsumer.as_asgi()),
]