import requests
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache

BASE_URL = "https://api.nasa.gov/planetary/apod"
CACHE_KEY = "nasa:apod:today"


@login_required
def get_apod(request):
    """Returns NASA's Astronomy Picture of the Day as JSON."""
    cached_apod = cache.get(CACHE_KEY)
    
    if cached_apod:
        return JsonResponse(cached_apod)
    
    query_params = {
        "thumbs": True,
        "api_key": settings.NASA_API_KEY
    }
    try:
        response = requests.get(BASE_URL, params=query_params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        media_type = data.get("media_type")
        
        if media_type == "image":
            image_url = data.get("hdurl") or data.get("url")
        elif media_type == "video":
            image_url = data.get("thumbnail_url")
        else:
            return JsonResponse({"error": "Unsupported APOD media type"}, status=400)
        
        if not image_url:
            return JsonResponse({"error": "No APOD image available"},status=404)
        
        result = {
            "title": data.get("title", "NASA APOD"),
            "image_url": image_url,
            "date": data.get("date"),
            "media_type": media_type,
            "explanation": data.get("explanation", ""),
        }
        
        cache.set(CACHE_KEY, result, 60 * 60 * 6)
        
        return JsonResponse(result)
        
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"NASA request failed: {str(e)}"}, status = 502)
    
    except ValueError:
        return JsonResponse({"error": "NASA returned invalid JSON"}, status = 502)
    
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)
    