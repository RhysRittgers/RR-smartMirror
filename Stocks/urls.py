from django.urls import path
from .views import *

urlpatterns = [
	path('user_stocks/', stock_prices, name='user_stocks'),
	path('add_stock/', add_stock, name='add_stock'),
	path('remove_stock/', remove_stock, name='remove_stock'),

	path('alerts/', stock_alerts, name='stock_alerts'),
	path('create_alert/', create_alert, name='create_alert'),
	path('remove_alert/', remove_alert, name='remove_alert'),
]