from django.urls import path
from .views import stock_prices

urlpatterns = [
	path('user_stocks/', stock_prices, name='user_stocks'),
]