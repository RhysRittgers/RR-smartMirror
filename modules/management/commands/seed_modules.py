from django.core.management.base import BaseCommand
from modules.models import ModuleCatalog

DEFAULTS = [
    {
        "key": "message",
        "name": "Custom Message",
        "description": "Display a user-defined message tile.",
        "settings_schema": {"message": {"type": "string"}},
    },
    {
        "key": "calendar",
        "name": "Calendar",
        "description": "Shows upcoming events for the week.",
        "settings_schema": {},
    },
    {
        "key": "weather",
        "name": "Weather",
        "description": "Current weather + details.",
        "settings_schema": {
            "city": {"type": "string"},
            "units": {"type": "string", "enum": ["imperial", "metric"]}
        },
    },
    {
        "key": "stocks",
        "name": "Stocks",
        "description": "Live stock prices for selected tickers.",
        "settings_schema": {
            "tickers": {"type": "array", "items": "string"}
        },
    },
    {
        "key": "spotify",
        "name": "Spotify Now Playing",
        "description": "Shows current track and playback state.",
        "settings_schema": {},
    },
    {
        "key": "oura",
        "name": "Oura Ring",
        "description": "Sleep, Readiness, and Activity scores.",
        "settings_schema": {
            "cards": {"type": "array", "items": {"enum": ["sleep","readiness","activity"]}}
        },
    },
]

class Command(BaseCommand):
    help = "Seed ModuleCatalog with default module definitions"

    def handle(self, *args, **kwargs):
        created = 0
        for entry in DEFAULTS:
            obj, was_created = ModuleCatalog.objects.get_or_create(
                key=entry["key"],
                defaults={
                    "name": entry["name"],
                    "description": entry["description"],
                    "settings_schema": entry["settings_schema"],
                },
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded modules. New entries: {created}"))
