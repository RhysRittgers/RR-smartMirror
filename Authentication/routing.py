from django.urls import path
from .mirror_login_consumer import MirrorLoginConsumer, SettingsConsumer

websocket_urlpatterns = [
    path("ws/mirror-login/", MirrorLoginConsumer.as_asgi()),
    path("ws/settings/", SettingsConsumer.as_asgi()),
]
