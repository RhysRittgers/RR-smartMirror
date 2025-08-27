# Authentication/routing.py
from django.urls import path
from .consumers import MirrorLoginConsumer, SettingsConsumer

websocket_urlpatterns = [
    path("ws/mirror-login/", MirrorLoginConsumer.as_asgi()),
    path("ws/settings/", SettingsConsumer.as_asgi()),
]
