from django.urls import path
from .views import mobile_dashboard

urlpatterns = [
    path('', mobile_dashboard, name='mobile_dashboard')
]