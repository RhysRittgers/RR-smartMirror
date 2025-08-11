from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse 

def home(request):
    host = request.get_host()
    print("👀 Mirror home hit. User:", request.user)
    print("Is user authenticated?", request.user.is_authenticated)
    print("Logged in user:", request.user)
    print(f" 🌐 host connected: {host}")
    
    if host.startswith("mirror."):
        if request.user.is_authenticated:
            return render(request, "index.html")
        else:
            return render(request, "mirror_login_waiting.html") #waiting screen when mirror connects
    else:
        return redirect("mobile_dashboard") #user remote login
    #else:
        #return HttpResponse("Invalid domain", status=400)
