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
from django.contrib.sessions.models import Session

User = get_user_model()

@csrf_exempt
def mirror_authenticate(request):
    
    if request.method == "POST":
        token = request.POST.get("token")
        print("Token received:", token)

        try:
            print("👀 Mirror secret key in use:", settings.SECRET_KEY)
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["user_id"])
            login(request, user)  # creates session for mirror

            request.session.save()

            print("Mirror user logged in:", user.username)
            print("request.user after login:", request.user)

            return JsonResponse({"status": "success"})
        except ExpiredSignatureError:
            return JsonResponse({"status": "expired"}, status=401)
        except (InvalidTokenError, User.DoesNotExist) as e:
            print("Invalid Token or user:", str(e))
            return JsonResponse({"status": "invalid"}, status=403)

    return JsonResponse({}, status=400)

@login_required
def generate_mirror_token(request):
    user_id = request.user.id

    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=5)  # expires in 1 minute
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    print("📦 Remote secret used to sign:", settings.SECRET_KEY)
    return JsonResponse({"token": token})

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            #broadcast login event to mirror via WebSocket group
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "mirror_login",
                {
                    "type": "login_success",
                    "username": user.username
                }
            )

            return JsonResponse({"success": True, "redirect": "/"})  #mirror loads dashboard
        else:
            return JsonResponse({"success": False, "error": "Invalid username or password."})

    return render(request, "login.html")


@ensure_csrf_cookie
def csrf_token_view(request):
    return JsonResponse({'csrfToken': request.META.get('CSRF_COOKIE', '')})


def logout_view(request):
    logout(request)
    return redirect('/')
