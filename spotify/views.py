# spotify/views.py
import os, time, json, secrets, urllib.parse, requests
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST

AUTH_URL  = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE  = "https://api.spotify.com/v1"
SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

def _set_tokens(session, token_info):
    # Save access/refresh + expiry in epoch seconds
    session["spotify_access_token"]  = token_info.get("access_token")
    session["spotify_refresh_token"] = token_info.get("refresh_token") or session.get("spotify_refresh_token")
    expires_in = token_info.get("expires_in", 3600)
    session["spotify_expires_at"]    = int(time.time()) + int(expires_in) - 30  # 30s safety
    session.modified = True

def _ensure_token(session):
    """Return a valid access token, refreshing with refresh_token if needed."""
    access = session.get("spotify_access_token")
    refresh = session.get("spotify_refresh_token")
    exp     = session.get("spotify_expires_at", 0)

    # no tokens yet
    if not access and not refresh:
        return None

    # still valid?
    if access and time.time() < (exp or 0):
        return access

    # refresh
    if not refresh:
        return None
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET,
    }
    r = requests.post(TOKEN_URL, data=data, timeout=15)
    if r.status_code != 200:
        return None
    payload = r.json()
    _set_tokens(session, payload)
    return session.get("spotify_access_token")

def _api_request(request, method, path, *, params=None, json_body=None):
    token = _ensure_token(request.session)
    if not token:
        return JsonResponse({"error": "not_authorized"}, status=401)
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{API_BASE}{path}"
    r = requests.request(method, url, headers=headers, params=params or {}, json=json_body, timeout=15)
    if r.status_code == 204:
        return JsonResponse({}, status=200)  # treat No Content as OK
    try:
        data = r.json() if r.content else {}
    except Exception:
        data = {}
    return JsonResponse(data, status=r.status_code)

@login_required
@require_GET
def spotify_login(request):
    state = secrets.token_urlsafe(16)
    request.session["spotify_oauth_state"] = state
    params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "show_dialog": "false",
    }
    return redirect(f"{AUTH_URL}?{urllib.parse.urlencode(params)}")

@login_required
@require_GET
def spotify_callback(request):
    # CSRF/state check
    if request.GET.get("state") != request.session.get("spotify_oauth_state"):
        return HttpResponseBadRequest("Invalid OAuth state")
    code = request.GET.get("code")
    if not code:
        return HttpResponseBadRequest("No code returned from Spotify")

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET,
    }
    r = requests.post(TOKEN_URL, data=data, timeout=15)
    if r.status_code != 200:
        return HttpResponseBadRequest(f"Token exchange failed: {r.text}")
    _set_tokens(request.session, r.json())
    return redirect("/Dashboard/")

@login_required
@require_GET
def current_track(request):
    # 200 with JSON of current track; {} if nothing playing
    return _api_request(request, "GET", "/me/player/currently-playing")

@login_required
@require_POST
def control(request):
    try:
        body = json.loads(request.body.decode() or "{}")
    except Exception:
        body = {}
    action = (body.get("action") or "").lower()
    path = {
        "play": "/me/player/play",
        "pause": "/me/player/pause",
        "next": "/me/player/next",
        "previous": "/me/player/previous",
    }.get(action)
    if not path:
        return HttpResponseBadRequest("Unsupported action")
    # For play with a specific context/uri, send json body; otherwise empty {} is fine
    return _api_request(request, "PUT", path, json_body=body.get("args"))
