from django.db import models #imports djangos built-in ORM for handling databases. Always need to include this
from django.contrib.auth.models import User #imports djangos built in user model so we can link events to specific users. We use this instead of a custom one because it already has built in security
from django.utils.timezone import now #imports a time model so our calendar can keep track of events based on real-time
from datetime import date

# Create your models here. #this is where we define the models (classes) that will create a table in our database

#this is the calendar table class to keep track of the user, event, time, etc.

class CalendarEvent(models.Model): #always use (models.Model) as it is a built in ORM that makes the database able to use django models.py features
	user			  = models.ForeignKey(User, on_delete=models.CASCADE) #links event to the appropriate user
	event_name		  = models.CharField(max_length=255) #event title
	event_date		  = models.DateField() #stores the date of the event so it can be displayed at the right time
	event_time		  = models.TimeField(blank=True, null=True)#optional input in case the event is an all day affair
	event_description = models.TextField(blank=True, null=True)#optional extra details. blank=true in django forms means this is optional, null=true means no description was entered
	date_created	  = models.DateTimeField(auto_now_add=True)#stores when the event was created for sorting/filtering purposes

	#function that tells django how the event should be displayed
	def __str__(self): #self represents current instance of the class. Allows access to variables and methods within that specific instance. __init__ is a custom class by python that formats how custom class objects are presented
		return f"{self.event_name} - {self.event_date} ({self.user.username})"

	#function that formats the events as a dictionary so it can be easily converted into JSON format
	def as_dict(self):
		return {
			"event_name": self.event_name,
			"event_date": self.event_date.strftime("%Y-%m-%d"),
			"event_time": self.event_time.strftime("%H:%M") if self.event_time else "All day",
			"event_description": self.event_description,
		}
	
