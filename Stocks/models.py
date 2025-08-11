from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class StockPreference(models.Model):
	user			  = models.ForeignKey(User, on_delete=models.CASCADE)
	stock_preference_one = models.CharField(max_length=100)
	stock_preference_two = models.CharField(max_length=100)
	stock_preference_three = models.CharField(max_length=100)
	stock_preference_four = models.CharField(max_length=100)

	def __str__(self):
		return(f"{self.user.username}' stock preferences'")
