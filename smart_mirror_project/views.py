from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from modules.models import UserModule

def home(request):
    host = request.get_host()

    if host.startswith("mirror."):
        if request.user.is_authenticated:
            # LIVE mirror -> pass the user's enabled modules
            modules = (
                UserModule.objects
                .select_related("module")
                .filter(user=request.user, enabled=True)
                .order_by("z", "y", "x")
            )
            # TEMP debug to verify in Render Logs:
            print("MIRROR HOME -> user:", getattr(request.user, "username", None),
                  "enabled modules:", modules.count())
            return render(request, "index_modular.html", {"modules": modules})
        else:
            return render(request, "mirror_login_waiting.html")

    # Remote UI
    return redirect("Dashboard:mobile_dashboard")

