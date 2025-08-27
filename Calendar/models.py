# Calendar/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import date


class CalendarEvent(models.Model):
    user              = models.ForeignKey(User, on_delete=models.CASCADE)
    event_name        = models.CharField(max_length=255)
    event_date        = models.DateField()
    event_time        = models.TimeField(blank=True, null=True)
    event_description = models.TextField(blank=True, null=True)
    date_created      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_name} - {self.event_date} ({self.user.username})"

    def as_dict(self):
        # IMPORTANT: return None for no time (not "All day") so the front-end
        # doesn't try to parse it as HH:MM and render NaN.
        return {
            "event_name": self.event_name,
            "event_date": self.event_date.strftime("%Y-%m-%d"),
            "event_time": self.event_time.strftime("%H:%M") if self.event_time else None,
            "event_description": self.event_description or "",
        }
