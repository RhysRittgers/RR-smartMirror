import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import UserModule

@require_POST
@login_required
def update_layout(request):
    """
    Accepts a JSON array of items: [{id,x,y,w,h}, ...] scoped to the current user.
    Saves new positions/sizes. Returns {"status":"ok"}.
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
        if not isinstance(payload, list):
            return HttpResponseBadRequest("Payload must be a list")
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    ids = [int(item.get("id")) for item in payload if "id" in item]
    items = {um.id: um for um in UserModule.objects.filter(user=request.user, id__in=ids)}

    for item in payload:
        um = items.get(int(item.get("id", -1)))
        if not um:
            continue
        um.x = int(item.get("x", um.x))
        um.y = int(item.get("y", um.y))
        um.w = int(item.get("w", um.w))
        um.h = int(item.get("h", um.h))
        um.save(update_fields=["x","y","w","h","updated_at"])

    return JsonResponse({"status": "ok"})
