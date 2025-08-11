from django.urls import path 
from .views import * #imports upcoming events method from views.py

urlpatterns = [
	path('upcoming_events/', upcoming_events, name='upcoming_events'),
	path('add-event/', add_event, name='add_event'),
]

