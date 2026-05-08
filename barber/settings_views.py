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

    def format_time(t):
        return t.strftime("%I:%M %p") if t else None

    response = {
        "setting": {
            "opening_time": format_time(settings_obj.opening_time) if settings_obj else None,

            "closing_time": format_time(settings_obj.closing_time) if settings_obj else None,

            "weekly_holiday": settings_obj.weekly_holiday if settings_obj else None,

            "slot_duration_minutes":
                settings_obj.slot_duration_minutes if settings_obj else None,

            "lunch_start_time":
                format_time(settings_obj.lunch_start_time)
                if settings_obj else None,

            "lunch_end_time":
                format_time(settings_obj.lunch_end_time)
                if settings_obj else None,
        },

    }

    return Response(response)




@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def save_settings(request):

    data = request.data
    setting_data = data.get("setting", {})

    settings_obj = BarberShopSettings.objects.first()

    opening = parse_time(setting_data.get("opening_time"))
    closing = parse_time(setting_data.get("closing_time"))

    lunch_start = parse_time(
        setting_data.get("lunch_start_time")
    )

    lunch_end = parse_time(
        setting_data.get("lunch_end_time")
    )

    if settings_obj:

        settings_obj.opening_time = opening
        settings_obj.closing_time = closing

        settings_obj.weekly_holiday = (
            setting_data.get("weekly_holiday")
        )

        settings_obj.slot_duration_minutes = (
            setting_data.get("slot_duration_minutes")
        )

        settings_obj.lunch_start_time = lunch_start
        settings_obj.lunch_end_time = lunch_end

        settings_obj.save()

    else:

        settings_obj = BarberShopSettings.objects.create(
            opening_time=opening,
            closing_time=closing,

            weekly_holiday=setting_data.get("weekly_holiday"),

            slot_duration_minutes=setting_data.get(
                "slot_duration_minutes"
            ),

            lunch_start_time=lunch_start,
            lunch_end_time=lunch_end
        )

    return Response({
        "message": "Settings saved successfully"
    })