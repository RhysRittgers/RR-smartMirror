from django.urls import path
from .consumers import SpotifyConsumer

websocket_urlpatterns = [
    path("ws/spotify/", SpotifyConsumer.as_asgi()),
]
