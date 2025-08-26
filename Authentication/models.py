from django.db import models

# Create your models here.
# Authentication/models.py
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="prefs")
    use_24h = models.BooleanField(default=False)  # False = 12h, True = 24h

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_prefs(sender, instance, created, **kwargs):
    if created:
        UserPreference.objects.get_or_create(user=instance)
