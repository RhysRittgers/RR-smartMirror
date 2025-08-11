from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import CustomMessage

def mirror_view(request):
    return render(request, 'index.html')

def dashboard_view(request):
    return render(request, 'dashboard.html')

@csrf_exempt
def update_message(request):
    print("🔥 update_message hit")
    print("User:", request.user)
    print("Is Authenticated:", request.user.is_authenticated)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    message = request.POST.get("message")
    print("📨 Received message:", message)

    if not message:
        return JsonResponse({"error": "No message provided"}, status=400)

    # Save to DB
    custom_message, created = CustomMessage.objects.get_or_create(user=request.user)
    custom_message.custom_message = message
    custom_message.save()
    print("💾 Saved to DB for user:", request.user.username)

    # Broadcast via WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "mirror_display",
        {
            "type": "broadcast_message",
            "message": message
        }
    )

    return JsonResponse({"status": "Message saved and broadcasted!"})

@csrf_exempt
def user_message(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    message = CustomMessage.objects.filter(user=request.user).first()
    return JsonResponse({
        "message": message.custom_message if message else " ",
        "is_visible": message.is_visible if message else False
    })

@csrf_exempt
def toggle_message(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method == "POST":
        message_obj = CustomMessage.objects.filter(user=request.user).first()
        if not message_obj:
            return JsonResponse({"success": False, "error": "Message not found"})

        message_obj.is_visible = not message_obj.is_visible
        message_obj.save()

        return JsonResponse({
            "success": True,
            "is_visible": message_obj.is_visible,
            "message": message_obj.custom_message
        })

    return JsonResponse({"success": False, "error": "POST method required"})
