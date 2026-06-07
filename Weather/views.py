from django.shortcuts import render
from django.http import JsonResponse 
from django.contrib.auth.decorators import login_required
from .models import WeatherPreference
from django.conf import settings
import requests

@login_required
def weather_preference(request):
    
    API_KEY = settings.WEATHER_API_KEY  # gets API key from settings

    # gets users weather preference
    weather_pref = WeatherPreference.objects.filter(user=request.user).first()

    if not weather_pref or not weather_pref.location:
        return JsonResponse({"error": "No location set in weather preferences."}, status=400)

    location = weather_pref.location  # gets preferred location from user
    unit = "metric" if weather_pref.unit == "Celsius" else "imperial"  # gets unit preference from user

    # call weather api
    WEATHER_API_URL = f"https://api.openweathermap.org/data/2.5/weather?q={location}&units={unit}&appid={API_KEY}"

    try:
        response = requests.get(WEATHER_API_URL)
        weather_data = response.json()

        # if api request fails, return an error
        if response.status_code != 200:
            return JsonResponse({"error": "Failed to retrieve weather data."}, status=500)

        # format JsonResponse based on user preference (moved outside the if statement)
        formatted_response = {
            "location": location,
            "temperature": weather_data["main"]["temp"],
            "unit": weather_pref.unit,
            "humidity": weather_data["main"]["humidity"] if weather_pref.show_humidity else "Hidden",
            "sunrise_sunset": {
                "sunrise": weather_data["sys"]["sunrise"],  # fixed typo from `asunrise`
                "sunset": weather_data["sys"]["sunset"]
            } if weather_pref.show_sunrise_sunset else "Hidden",
            "forcast": weather_data["weather"][0]["description"] if weather_pref.show_forcast else "Hidden"
        }

        return JsonResponse(formatted_response)

    except requests.exceptions.RequestException:
        return JsonResponse({"error": "Error connecting to weather API"}, status=500)
