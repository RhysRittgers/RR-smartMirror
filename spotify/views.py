# spotify/views.py
import time
import requests
import urllib.parse
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_ME_PLAYER = "https://api.spotify.com/v1/me/player"
SPOTIFY_CURRENT = "https://api.spotify.com/v1/me/player/currently-playing"

SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing streaming"

def spotify_login(request):
    params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": SCOPES,
    }
    return redirect(f"https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params)}")

@login_required
def spotify_callback(request):
    code = request.GET.get("code")
    if not code:
        # surface the problem instead of silently redirecting
        err = request.GET.dict()
        return JsonResponse({"error": "No code from Spotify", "query": err}, status=400)

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET,
    }
    r = requests.post(SPOTIFY_TOKEN_URL, data=data)
    try:
        token_info = r.json()
    except Exception:
        return JsonResponse({"error": "Non-JSON token response", "status": r.status_code, "text": r.text}, status=500)

    if r.status_code != 200 or "access_token" not in token_info:
        return JsonResponse({"error": "Token exchange failed", "status": r.status_code, "body": token_info}, status=400)

    # Save to session (shared across mirror & remote)
    request.session["spotify_access_token"]  = token_info["access_token"]
    request.session["spotify_refresh_token"] = token_info.get("refresh_token")
    # store approximate expiry epoch
    request.session["spotify_expires_at"]    = int(time.time()) + int(token_info.get("expires_in", 3600)) - 60
    request.session["spotify_token_raw"]     = token_info  # handy for debugging
    request.session.save()

    return redirect("/Dashboard/")

def _session_tokens(request):
    return (
        request.session.get("spotify_access_token"),
        request.session.get("spotify_refresh_token"),
        request.session.get("spotify_expires_at"),
    )

def _ensure_access_token(request):
    """Refresh if expired. Returns access_token or None."""
    access, refresh, expires_at = _session_tokens(request)
    now = int(time.time())

    if access and expires_at and now < int(expires_at):
        return access

    if not refresh:
        return None

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET,
    }
    r = requests.post(SPOTIFY_TOKEN_URL, data=data)
    info = r.json()
    if r.status_code != 200 or "access_token" not in info:
        # don’t blow up—just clear broken tokens
        for k in ("spotify_access_token","spotify_refresh_token","spotify_expires_at"):
            request.session.pop(k, None)
        request.session.save()
        return None

    request.session["spotify_access_token"] = info["access_token"]
    if "refresh_token" in info:
        request.session["spotify_refresh_token"] = info["refresh_token"]
    request.session["spotify_expires_at"] = int(time.time()) + int(info.get("expires_in", 3600)) - 60
    request.session.save()
    return request.session["spotify_access_token"]

@login_required
def spotify_debug(request):
    access, refresh, expires_at = _session_tokens(request)
    return JsonResponse({
        "whoami": request.user.username if request.user.is_authenticated else "AnonymousUser",
        "session_key": request.session.session_key,
        "has_access_token": bool(access),
        "has_refresh_token": bool(refresh),
        "expires_at": expires_at,
        "token_raw_present": bool(request.session.get("spotify_token_raw")),
    })

@login_required
def current_track(request):
    token = _ensure_access_token(request)
    if not token:
        return JsonResponse({"error": "no_token"}, status=401)

    r = requests.get(SPOTIFY_CURRENT, headers={"Authorization": f"Bearer {token}"})
    if r.status_code == 204:
        return JsonResponse({"playing": False, "track": None})
    try:
        data = r.json()
    except Exception:
        return JsonResponse({"error": "bad_response", "status": r.status_code, "text": r.text}, status=502)

    item = data.get("item") or {}
    return JsonResponse({
        "is_playing": data.get("is_playing"),
        "progress_ms": data.get("progress_ms"),
        "track": {
            "name": item.get("name"),
            "artists": [a.get("name") for a in (item.get("artists") or [])],
            "album": (item.get("album") or {}).get("name"),
            "image": ((item.get("album") or {}).get("images") or [{}])[0].get("url"),
        }
    })
