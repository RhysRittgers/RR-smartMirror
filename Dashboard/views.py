from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
import json

# NEW: models for the store
from modules.models import ModuleCatalog, UserModule


# --- Existing remote home ---
@csrf_exempt
@login_required
def mobile_dashboard(request):
    return render(request, "mobile_dashboard.html")


# --- App Store page ---
@login_required
def app_store(request):
    catalog = ModuleCatalog.objects.all().order_by("name")
    # Map {module_id: UserModule} for the current user so template can show install/enable state
    user_modules = {um.module_id: um for um in UserModule.objects.filter(user=request.user)}
    return render(request, "remote/app_store.html", {"catalog": catalog, "user_modules": user_modules})


# --- Toggle install/enable for a module ---
@login_required
def toggle_module(request, module_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    mod = get_object_or_404(ModuleCatalog, id=module_id)
    um, created = UserModule.objects.get_or_create(user=request.user, module=mod)
    um.enabled = True if created else not um.enabled
    if created:
        # default placement
        um.x, um.y, um.w, um.h = 0, 0, 4, 3
    um.save()
    return JsonResponse({"enabled": um.enabled, "user_module_id": um.id})


# --- Save per-module settings JSON into UserModule.settings ---
@login_required
def save_module_settings(request, user_module_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    um = get_object_or_404(UserModule, id=user_module_id, user=request.user)
    try:
        data = json.loads(request.body.decode("utf-8"))
        if not isinstance(data, dict):
            return HttpResponseBadRequest("Settings must be an object")
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")
    um.settings = data
    um.save(update_fields=["settings", "updated_at"])
    return JsonResponse({"status": "ok"})
