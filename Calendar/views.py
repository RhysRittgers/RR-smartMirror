# Calendar/views.py
from django.shortcuts import render
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
    # Use local date (respects TIME_ZONE) so "today" doesn't slip due to UTC.
    today = timezone.localdate()
    next_week = today + timedelta(days=7)

    events = CalendarEvent.objects.filter(
        event_date__range=[today, next_week],
        user=request.user
    )

    event_dict = {}
    for event in events:
        event_day = event.event_date.strftime("%A")
        event_dict.setdefault(event_day, []).append(event.as_dict())

    # Build 7-day rolling window starting from 'today'
    week_data = {}
    for i in range(7):
        day = today + timedelta(days=i)
        weekday_name = day.strftime("%A")
        week_data[weekday_name] = event_dict.get(weekday_name, ["No events scheduled"])

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

    # Save to DB
    event = CalendarEvent.objects.create(
        user=request.user,
        event_name=name,
        event_date=event_date,
        event_time=event_time,
        event_description=desc
    )

    # Broadcast to all mirrors
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "mirror_calendar",
        {
            "type": "calendar_event",
            "event": event.as_dict(),
        }
    )

    return JsonResponse({"status": "Event saved and broadcasted!"})
