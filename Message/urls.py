from django.urls import path 
from .views import *
	
urlpatterns = [
	path('user_message/', user_message, name='user_message'),
	path('toggle_message/', toggle_message, name='toggle_message'),
	path('update-message/', update_message, name='update_message'),
]