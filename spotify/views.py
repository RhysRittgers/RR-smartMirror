# views.py

import requests
import urllib.parse
from django.conf import settings
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required

def spotify_login(request):
    scopes = "user-read-playback-state user-modify-playback-state user-read-currently-playing streaming"
    params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": scopes,
    }
    url = f"https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params)}"
    return redirect(url)


def spotify_callback(request):
    code = request.GET.get("code")

    if not code:
        return HttpResponse("No code returned from Spotify", status=400)

    token_url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET,
    }

    response = requests.post(token_url, data=data)
    token_info = response.json()

    # OPTIONAL: store in session for now
    request.session["spotify_access_token"] = token_info.get("access_token")
    request.session["spotify_refresh_token"] = token_info.get("refresh_token")

    return redirect("/Dashboard/")  # or your remote dashboard

@login_required
def current_track(request):
    # TODO: replace with real Spotify logic
    return JsonResponse({"track": None, "status": "not_implemented"}, status=200)
