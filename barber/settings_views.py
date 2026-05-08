from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
from accounts.permissions import *
from rest_framework.response import Response
from .models import *


# Helper function to handle conversion
def parse_time(time_str):
    if not time_str:
        return None
    # %I is 12-hour clock, %M is minutes, %p is AM/PM
    return datetime.strptime(time_str, "%I:%M %p").time()


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def get_settings(request):
    settings_obj = BarberShopSettings.objects.first()
    if not settings_obj:
        return Response({})

    # Helper to format time safely (handles None values)
    def format_time(t):
        return t.strftime("%I:%M %p") if t else None

    return Response({
        "opening_time": format_time(settings_obj.opening_time),
        "closing_time": format_time(settings_obj.closing_time),

        "lunch_start_time": format_time(settings_obj.lunch_start_time),
        "lunch_end_time": format_time(settings_obj.lunch_end_time),

        "slot_duration": settings_obj.slot_duration,
        "week_holiday": settings_obj.week_holiday
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def save_settings(request):
    data = request.data
    settings_obj = BarberShopSettings.objects.first()

    # Parse all time strings from the request
    # Note: Ensure keys match the JSON in WhatsApp Image 2026-05-06 at 10.48.45 AM.jpeg
    opening = parse_time(data.get('opening_time'))
    closing = parse_time(data.get('closing_time'))
    l_start = parse_time(data.get('lunch_start_time'))
    l_end = parse_time(data.get('lunch_end_time'))

    if settings_obj:
        settings_obj.opening_time = opening
        settings_obj.closing_time = closing
        settings_obj.lunch_start_time = l_start
        settings_obj.lunch_end_time = l_end
        settings_obj.slot_duration = data.get('slot_duration')
        settings_obj.week_holiday = data.get('week_holiday')
        settings_obj.save()
    else:
        settings_obj = BarberShopSettings.objects.create(
            opening_time=opening,
            closing_time=closing,
            lunch_start_time=l_start,
            lunch_end_time=l_end,
            slot_duration=data.get('slot_duration'),
            week_holiday=data.get('week_holiday')
        )
        
    return Response({'message': 'Settings saved successfully!!!'})