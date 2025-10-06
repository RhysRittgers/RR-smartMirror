from django.conf import settings
from django.db import models

class ModuleCatalog(models.Model):
    key = models.SlugField(unique=True)           # e.g. "weather", "stocks", "message", "calendar", "spotify", "oura"
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=20, default="1.0.0")
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True)  # optional name of an icon (or URL)
    settings_schema = models.JSONField(default=dict)     # JSON schema-like dict for remote UI

    def __str__(self):
        return f"{self.name} ({self.key})"

class UserModule(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    module = models.ForeignKey(ModuleCatalog, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=True)

    # Grid placement (12-col grid suggested)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    w = models.IntegerField(default=4)
    h = models.IntegerField(default=3)
    z = models.IntegerField(default=0)  # stacking / render order if needed

    # Per-installation settings (e.g. {"city": "San Diego", "units": "imperial"})
    settings = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "module")

    def __str__(self):
        return f"{self.user} · {self.module.key}"
