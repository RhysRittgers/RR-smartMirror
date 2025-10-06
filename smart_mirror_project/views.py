from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

def home(request):
    host = request.get_host()
    # print("👀 Mirror home hit. User:", request.user)

    if host.startswith("mirror."):
        if request.user.is_authenticated:
            # Use the modular layout as the LIVE mirror UI
            return render(request, "index_modular.html")
        else:
            # Waiting screen when mirror connects but user not logged in yet
            return render(request, "mirror_login_waiting.html")
    else:
        # Remote UI
        return redirect("Dashboard:mobile_dashboard")

@login_required
def mirror_modular_preview(request):
    # Leave this route for quick testing from the remote
    return render(request, "index_modular.html")
