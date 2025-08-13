# smart_mirror_project/diag.py
import hashlib
from django.http import JsonResponse
from django.conf import settings

def _fp(s: str) -> str:
    return hashlib.sha256((s or "").encode()).hexdigest()[:12]

def diag(request):
    db = settings.DATABASES["default"]
    return JsonResponse({
        # What Django thinks about THIS request:
        "whoami": request.user.username if request.user.is_authenticated else "AnonymousUser",
        "request_session_key": request.session.session_key,
        "cookie_sessionid": request.COOKIES.get("sessionid"),

        # Session/cookie config:
        "SESSION_ENGINE": getattr(settings, "SESSION_ENGINE", "django.contrib.sessions.backends.db"),
        "SESSION_COOKIE_NAME": settings.SESSION_COOKIE_NAME,
        "SESSION_COOKIE_DOMAIN": settings.SESSION_COOKIE_DOMAIN,
        "SESSION_COOKIE_SAMESITE": settings.SESSION_COOKIE_SAMESITE,

        # DB in use:
        "DB_ENGINE": db.get("ENGINE"),
        "DB_NAME": db.get("NAME"),
        "DB_HOST": db.get("HOST"),
        "DB_PORT": db.get("PORT"),

        # Fingerprint only (confirms both services use same key)
        "SECRET_KEY_fp": _fp(settings.SECRET_KEY),
    })
