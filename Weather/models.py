from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class WeatherPreference(models.Model):
	user	 = models.OneToOneField(User, on_delete=models.CASCADE)

	location = models.CharField(max_length=100, blank=True, null=True)
	unit	 = models.CharField(max_length=50, default='Fahrenheit')

	#Booleans
	show_humidity		= models.BooleanField(default=False)
	show_sunrise_sunset = models.BooleanField(default=False)
	show_forcast		= models.BooleanField(default=False)

	def __str__(self):
		return f"{self.user.username}'s weather preferences"