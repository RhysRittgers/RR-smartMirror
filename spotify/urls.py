from django.urls import path
from . import views
app_name = "spotify"

urlpatterns = [
    path("login/", views.spotify_login, name="login"),
    path("callback/", views.spotify_callback, name="callback"),
    path("current/", views.current_track, name="current"),
    path("control/", views.control, name="control"),   # POST {"action":"pause"|...}
]
