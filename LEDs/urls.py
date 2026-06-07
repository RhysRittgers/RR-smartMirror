from django.urls import path 
from .views import *


urlpatterns = [
    path('turn_on/', turn_on, name='turn_on'),
    path('turn_off/', turn_off, name='turn_off'),
    path('party_mode/', party_mode, name='party_mode'),
    path('vanity/', vanity, name='vanity'),
    path('custom_color/', custom_color, name='custom_color')
]
