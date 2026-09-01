from django.urls import path
from .views import weather_preference, weekly_forecast

urlpatterns = [
	path('user_weather/', weather_preference, name='user_weather'),
	path('forecast/', weekly_forecast, name='forecast'),
]