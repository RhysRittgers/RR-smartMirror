from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta, datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import CalendarEvent


@login_required
def upcoming_events(request):
    """
    Return events for the current week (Mon -> Sun) in the project's TIME_ZONE.
    Frontend renders a fixed-week grid and expects all days of this week,
    not just 'today -> +7'.
    """
    # Local date in settings.TIME_ZONE
    today_local = timezone.localtime().date()          # respects TIME_ZONE
    # Monday=0 … Sunday=6
    week_start = today_local - timedelta(days=today_local.weekday())
    week_end   = week_start + timedelta(days=6)

    qs = (
        CalendarEvent.objects
        .filter(user=request.user, event_date__range=[week_start, week_end])
        .order_by('event_date', 'event_time')
    )

    # Build dict for the fixed week
    week_labels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    week_data = {label: [] for label in week_labels}

    for ev in qs:
        day_name = ev.event_date.strftime('%A')
        if day_name in week_data:
            week_data[day_name].append(ev.as_dict())

    # Frontend shows a placeholder when the list is empty, so leave [] for empty days
    return JsonResponse({"Week": week_data})


@csrf_exempt
@login_required
def add_event(request):
    if request.method != "POST":
        return HttpResponse("Invalid method", status=405)

    name = request.POST.get("event_name")
    date_str = request.POST.get("event_date")
    time_str = request.POST.get("event_time")
    desc = request.POST.get("event_description")

    if not name or not date_str:
        return HttpResponse("Missing required fields", status=400)

    try:
        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        event_time = datetime.strptime(time_str, "%H:%M").time() if time_str else None
    except ValueError as e:
        return HttpResponse(f"Invalid date/time format: {e}", status=400)

    # Save
    event = CalendarEvent.objects.create(
        user=request.user,
        event_name=name,
        event_date=event_date,
        event_time=event_time,
        event_description=desc
    )

    # Broadcast live to mirrors via this service's channel layer (best effort)
    channel_layer = get_channel_layer()
    if channel_layer is not None:
        async_to_sync(channel_layer.group_send)(
            "mirror_calendar",
            {"type": "calendar_event", "event": event.as_dict()}
        )

    # 🔥 IMPORTANT: return the event so the remote can push it via WebSocket
    return JsonResponse({
        "status": "Event saved and broadcasted!",
        "event": event.as_dict()
    })
