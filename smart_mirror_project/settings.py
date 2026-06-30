"""
Django settings for smart_mirror_project project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

# --------------------
# Core / Secrets
# --------------------
SECRET_KEY = os.getenv("SECRET_KEY", "insecure-default-key")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "dummy-weather-key")
STOCKS_API_KEY  = os.getenv("STOCKS_API_KEY",  "dummy-stocks-key")
NASA_API_KEY = os.getenv("NASA_API_KEY", "dummy-nasa-key")


DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost").split(",")
CSRF_TRUSTED_ORIGINS = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost").split(",")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# custom login url
LOGIN_URL = "/auth/login/"

# --------------------
# Apps
# --------------------
INSTALLED_APPS = [
    "corsheaders",
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # myapps
    "profiles",
    "Calendar",
    "Message",
    "Stocks",
    "Weather",
    "Authentication",
    "spotify",
    "Dashboard",
]

ASGI_APPLICATION = "smart_mirror_project.asgi.application"

# --------------------
# Middleware
# --------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

ROOT_URLCONF = "smart_mirror_project.urls"

# --------------------
# Templates
# --------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "smart_mirror_project.wsgi.application"

# --------------------
# Database
# --------------------
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}

# --------------------
# Password validation
# --------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------
# I18N / TZ
# --------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "EST"
USE_I18N = True
USE_TZ = True

# --------------------
# Static
# --------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------
# Channels
# --------------------
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
}

# --------------------
# CORS
# --------------------
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://remote.rr-smartmirror.com",  # remote subdomain
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://remote\.rr-smartmirror\.com$",
]

# --------------------
# Spotify
# --------------------
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# ----------------------------------------------------------
# Local development helpers (only apply when DEBUG=True)
# ----------------------------------------------------------
if DEBUG:
    # allow localhost and 127.0.0.1 hosts
    ALLOWED_HOSTS = list(set(ALLOWED_HOSTS) | {"127.0.0.1", "localhost"})

    # trust local origins for CSRF (with and without port)
    CSRF_TRUSTED_ORIGINS = list(set(CSRF_TRUSTED_ORIGINS) | {
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://localhost",
        "http://localhost:8000",
    })

# ----------------------------------------------------------
# Cookie / CSRF settings: prod vs. local (FINAL authority)
#   - This block should be near the bottom so its values win.
# ----------------------------------------------------------
if not DEBUG:
    # Production: real domain + secure cookies
    SESSION_COOKIE_DOMAIN = ".rr-smartmirror.com"
    CSRF_COOKIE_DOMAIN = ".rr-smartmirror.com"
    SESSION_COOKIE_SAMESITE = "None"
    CSRF_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    # Local dev: cookies work on http://127.0.0.1 / http://localhost
    SESSION_COOKIE_DOMAIN = None
    CSRF_COOKIE_DOMAIN = None
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
