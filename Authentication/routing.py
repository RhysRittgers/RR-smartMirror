# Authentication/routing.py
from django.urls import re_path
from Authentication.consumers import MirrorLoginConsumer

websocket_urlpatterns = [
    re_path(r"ws/mirror-login/$", MirrorLoginConsumer.as_asgi()),
]
