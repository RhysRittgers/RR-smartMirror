# Authentication/views.py
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from django.views.decorators.http import require_http_methods
from .models import UserPreference

User = get_user_model()

@csrf_exempt
def mirror_authenticate(request):
    if request.method == "POST":
        token = request.POST.get("token")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["user_id"])
            login(request, user)  # creates session for this client
            request.session.save()
            return JsonResponse({"status": "success"})
        except ExpiredSignatureError:
            return JsonResponse({"status": "expired"}, status=401)
        except (InvalidTokenError, User.DoesNotExist):
            return JsonResponse({"status": "invalid"}, status=403)
    return JsonResponse({}, status=400)

@login_required
def generate_mirror_token(request):
    payload = {
        "user_id": request.user.id,
        "exp": datetime.utcnow() + timedelta(minutes=5),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return JsonResponse({"token": token})

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # optional: broadcast login event
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "mirror_login",
                {"type": "login_success", "username": user.username}
            )
            return JsonResponse({"success": True, "redirect": "/"})
        else:
            return JsonResponse({"success": False, "error": "Invalid username or password."})
    return render(request, "login.html")

@ensure_csrf_cookie
def csrf_token_view(request):
    return JsonResponse({'csrfToken': request.META.get('CSRF_COOKIE', '')})

def logout_view(request):
    logout(request)
    return redirect('/')

@login_required
@require_http_methods(["GET", "POST"])
def time_format(request):
    """Stores user time preference and broadcasts it live via Channels."""
    prefs, _ = UserPreference.objects.get_or_create(user=request.user)
    if request.method == "POST":
        val = str(request.POST.get("use_24h", "")).lower()
        prefs.use_24h = val in ("1", "true", "yes", "on")
        prefs.save()
        # broadcast to mirrors
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "mirror_settings",
            {"type": "time_pref", "use_24h": prefs.use_24h}
        )
    return JsonResponse({"use_24h": prefs.use_24h})
