from django.contrib import admin
from .models import WeatherPreference, WeeklyForecastPreference

admin.site.register(WeatherPreference)
admin.site.register(WeeklyForecastPreference)