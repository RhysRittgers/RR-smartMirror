from django.shortcuts import render
from django.http import JsonResponse 
from django.contrib.auth.decorators import login_required
from .models import WeatherPreference, WeeklyForecastPreference
from django.conf import settings
import requests
import openmeteo_requests
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

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
    
    
    
# Open-Meteo 7 day forecast. Eventually will feed into the same system as the calendar allowing the jarvis system to help with schedule planning.
@login_required
def weekly_forecast(request):
    #Get user forecast preferences
    user_forecast = WeeklyForecastPreference.objects.filter(user=request.user).first()
    
    if not user_forecast:
        return JsonResponse(
            {
                "error":
                "No weekly forecast preferences found."
            },
            status=400
        )
    
    #setup open-meteo api client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)
    
    #Make sure all required weather variables are listed here 
    #The order of variables in hourly or daily is important to assign them correctly below 
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": user_forecast.latitude,
        "longitude": user_forecast.longitude,
        
        "daily": [
            "weather_code", 
            "temperature_2m_max", 
            "temperature_2m_min", 
            "precipitation_probability_max",
            "uv_index_max", 
            "rain_sum", 
            "showers_sum", 
            "sunset", 
            "sunrise", 
            "moon_phase", 
            "wind_speed_10m_max", 
            "wind_direction_10m_dominant"
        ],
        
        "forecast_days": 7,
        "timezone": "auto",
        "wind_speed_unit": user_forecast.wind_speed_unit,
        "temperature_unit": "fahrenheit",
        "precipitation_unit": user_forecast.precipitation_unit,
    }
    responses = openmeteo.weather_api(url,params=params)
    
    response = responses[0]
    
    daily = response.Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_max = daily.Variables(1).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(2).ValuesAsNumpy()
    daily_precipitation_probability_max = daily.Variables(3).ValuesAsNumpy()
    daily_uv_index_max = daily.Variables(4).ValuesAsNumpy()
    daily_rain_sum = daily.Variables(5).ValuesAsNumpy()
    daily_showers_sum = daily.Variables(6).ValuesAsNumpy()
    daily_sunset = daily.Variables(7).ValuesInt64AsNumpy()
    daily_sunrise = daily.Variables(8).ValuesInt64AsNumpy()
    daily_moon_phase = daily.Variables(9).ValuesAsNumpy()
    daily_wind_speed_10m_max = daily.Variables(10).ValuesAsNumpy()
    daily_wind_direction_10m_dominant = daily.Variables(11).ValuesAsNumpy()
    
    forecast_timezone = ZoneInfo(
        response.Timezone().decode()
    )

    start_date = datetime.fromtimestamp(
        daily.Time(),
        tz=timezone.utc
    ).astimezone(
        forecast_timezone
    )
    
    forecast = []
    
    for i in range(7):
        date = start_date + timedelta(days=i)
        day = {
            "date": date.strftime("%Y-%m-%d"),
            
            "weather_code": int(daily_weather_code[i]),
            
            "temperature_max": float(
                daily_temperature_2m_max[i]
            ),
            
            "temperature_min": float(
                daily_temperature_2m_min[i]
            ),
            
            "precipitation_probability": float(
                daily_precipitation_probability_max[i]
            ),
            
            "uv_index_max": float(
                daily_uv_index_max[i]
            ),
            
            "rain_sum": float(
                daily_rain_sum[i]
            ),
            
            "showers_sum": float(
                daily_showers_sum[i]
            ),
            
            "sunrise": int(
                daily_sunrise[i]
            ),
            
            "sunset": int(
                daily_sunset[i]
            ),
            
            "moon_phase": float(
                daily_moon_phase[i]
            ),
            
            "wind_speed_max": float(
                daily_wind_speed_10m_max[i]
            ),
            
            "wind_direction": float(
                daily_wind_direction_10m_dominant[i]
            ),
        }
        forecast.append(day)
    
    return JsonResponse({
        "location": user_forecast.location,
        "forecast": forecast
    })