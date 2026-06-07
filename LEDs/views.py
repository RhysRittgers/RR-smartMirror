from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def broadcast_led_command(command, payload=None):
    channel_layer = get_channel_layer()

    if channel_layer is not None:
        async_to_sync(channel_layer.group_send)(
            "led_commands",
            {
                "type": "led_command",
                "command": command,
                "payload": payload or {}
            }
        )


@csrf_exempt
@login_required
def turn_on(request):
    if request.method != "POST":
        return HttpResponse("Invalid method", status=405)

    broadcast_led_command("turn_on")
    return JsonResponse({"status": "LED command sent", "command": "turn_on"})


@csrf_exempt
@login_required
def turn_off(request):
    if request.method != "POST":
        return HttpResponse("Invalid method", status=405)

    broadcast_led_command("turn_off")
    return JsonResponse({"status": "LED command sent", "command": "turn_off"})


@csrf_exempt
@login_required
def vanity(request):
    if request.method != "POST":
        return HttpResponse("Invalid method", status=405)

    broadcast_led_command("vanity")
    return JsonResponse({"status": "LED command sent", "command": "vanity"})


@csrf_exempt
@login_required
def party_mode(request):
    if request.method != "POST":
        return HttpResponse("Invalid method", status=405)

    broadcast_led_command("party_mode")
    return JsonResponse({"status": "LED command sent", "command": "party_mode"})


@csrf_exempt
@login_required
def custom_color(request):
    if request.method != "POST":
        return HttpResponse("Invalid method", status=405)

    try:
        red = int(request.POST.get("red", 0))
        green = int(request.POST.get("green", 0))
        blue = int(request.POST.get("blue", 0))
        white = int(request.POST.get("white", 0))
    except ValueError:
        return JsonResponse({"error": "Color values must be integers"}, status=400)

    # Clamp values to 0-255
    red = max(0, min(255, red))
    green = max(0, min(255, green))
    blue = max(0, min(255, blue))
    white = max(0, min(255, white))

    payload = {
        "red": red,
        "green": green,
        "blue": blue,
        "white": white,
    }

    broadcast_led_command("custom_color", payload)
    return JsonResponse({
        "status": "LED command sent",
        "command": "custom_color",
        "payload": payload
    })