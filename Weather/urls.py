from django.urls import path
from .views import weather_preference

urlpatterns = [
	path('user_weather/', weather_preference, name='user_weather'),
]