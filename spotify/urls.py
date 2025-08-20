# spotify/urls.py
from django.urls import path
from . import views

app_name = "spotify"

urlpatterns = [
    path("login/", views.spotify_login, name="login"),
    path("callback/", views.spotify_callback, name="callback"),
    path("debug/", views.spotify_debug, name="debug"),
    path("current/", views.current_track, name="current"),
    path("devices/", views.devices, name="devices"),
    path("state/", views.state, name="state"),
    path("control/<str:action>/", views.control, name="control"),
]
