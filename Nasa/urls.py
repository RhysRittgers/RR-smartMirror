from django.urls import path
from .views import get_apod

urlpatterns = [
    path('apod/', get_apod, name='get_apod')
]