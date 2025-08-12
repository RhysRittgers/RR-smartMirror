from django.urls import path
from .views import mobile_dashboard

app_name = "Dashboard"

urlpatterns = [
    path('', mobile_dashboard, name='mobile_dashboard')
]