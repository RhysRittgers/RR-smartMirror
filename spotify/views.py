# spotify/views.py
import time
import requests
import urllib.parse
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_ME_PLAYER = "https://api.spotify.com/v1/me/player"
SPOTIFY_CURRENT = "https://api.spotify.com/v1/me/player/currently-playing"

SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing streaming"

@login_required
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

SPOTIFY_DEVICES     = "https://api.spotify.com/v1/me/player/devices"
SPOTIFY_PLAYER      = "https://api.spotify.com/v1/me/player"
SPOTIFY_NEXT        = "https://api.spotify.com/v1/me/player/next"
SPOTIFY_PREVIOUS    = "https://api.spotify.com/v1/me/player/previous"
SPOTIFY_PLAY        = "https://api.spotify.com/v1/me/player/play"
SPOTIFY_PAUSE       = "https://api.spotify.com/v1/me/player/pause"
SPOTIFY_TRANSFER    = "https://api.spotify.com/v1/me/player"
SPOTIFY_SEEK        = "https://api.spotify.com/v1/me/player/seek"
SPOTIFY_VOLUME      = "https://api.spotify.com/v1/me/player/volume"

def _spotify_api(request, method, url, **kw):
    token = _ensure_access_token(request)
    if not token:
        return None, {"error": "no_token"}, 401
    headers = kw.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    r = requests.request(method, url, headers=headers, **kw)
    try:
        body = r.json() if r.text else {}
    except Exception:
        body = {"raw": r.text}
    return r, body, r.status_code

def _normalize_state(json_obj):
    if not json_obj:
        return {"playing": False, "track": None}
    item = (json_obj or {}).get("item") or {}
    return {
        "is_playing": json_obj.get("is_playing"),
        "progress_ms": json_obj.get("progress_ms"),
        "device": (json_obj.get("device") or {}).get("name"),
        "track": {
            "name": item.get("name"),
            "artists": [a.get("name") for a in (item.get("artists") or [])],
            "album": (item.get("album") or {}).get("name"),
            "image": ((item.get("album") or {}).get("images") or [{}])[0].get("url"),
        }
    }

@login_required
def devices(request):
    r, body, status = _spotify_api(request, "GET", SPOTIFY_DEVICES)
    return JsonResponse(body, status=status)

@login_required
def state(request):
    r, body, status = _spotify_api(request, "GET", SPOTIFY_PLAYER)
    if status == 204:  # no active device
        return JsonResponse({"is_playing": False, "track": None})
    return JsonResponse(_normalize_state(body), status=200 if status == 200 else status)

@login_required
def control(request, action):
    # Map simple actions to endpoints
    routes = {
        "next":  ("POST", SPOTIFY_NEXT, {}),
        "prev":  ("POST", SPOTIFY_PREVIOUS, {}),
        "play":  ("PUT",  SPOTIFY_PLAY, {"json": {}}),
        "pause": ("PUT",  SPOTIFY_PAUSE, {}),
    }
    if action == "seek":
        ms = int(request.GET.get("ms", "0"))
        method, url, extra = "PUT", f"{SPOTIFY_SEEK}?position_ms={ms}", {}
    elif action == "volume":
        vol = int(request.GET.get("v", "50"))
        method, url, extra = "PUT", f"{SPOTIFY_VOLUME}?volume_percent={vol}", {}
    elif action == "transfer":
        device_id = request.GET.get("device_id")
        if not device_id:
            return JsonResponse({"error": "device_id required"}, status=400)
        method, url, extra = "PUT", SPOTIFY_TRANSFER, {"json": {"device_ids": [device_id], "play": True}}
    else:
        if action not in routes:
            return JsonResponse({"error": "unknown_action"}, status=400)
        method, url, extra = routes[action]

    r, body, status = _spotify_api(request, method, url, **extra)
    if status not in (200, 201, 202, 204):
        return JsonResponse({"error": "spotify_error", "status": status, "body": body}, status=400)

    # pull fresh state and broadcast to mirror via Channels
    r2, body2, st2 = _spotify_api(request, "GET", SPOTIFY_PLAYER)
    norm = _normalize_state(body2) if st2 == 200 else {"is_playing": False, "track": None}

    channel_layer = get_channel_layer()
    # Per-user group
    async_to_sync(channel_layer.group_send)(
        f"user_{request.user.id}",
        {"type": "spotify.update", "payload": norm}
    )
    # Shared mirror group (optional, if your consumer also joins this)
    async_to_sync(channel_layer.group_send)(
        "mirror_spotify",
        {"type": "spotify.update", "payload": norm}
    )

    return JsonResponse({"ok": True, "state": norm})
