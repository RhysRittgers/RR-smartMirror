from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def mobile_dashboard(request):
    return render(request, 'mobile_dashboard.html')