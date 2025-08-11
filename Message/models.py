from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class CustomMessage(models.Model):
	user		   = models.OneToOneField(User, on_delete=models.CASCADE) #links to the appropriate user using foriegn key
	custom_message = models.TextField() #text field so the message can be longer 
	is_visible = models.BooleanField(default=True)

	def __str__(self):
		
		return f"{self.custom_message}"

	def as_dict(self):
		
		return {
			"custom_message": self.custom_message,
			"is_visible": self.is_visible,
		}
