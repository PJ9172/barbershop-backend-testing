from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import *
from rest_framework.response import Response
from .models import *


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def get_settings(request):
    settings_obj = BarberShopSettings.objects.first()
    if not settings_obj:
        return Response({})
    
    return Response({
        "opening_time": settings_obj.opening_time,
        "closing_time": settings_obj.closing_time,

        "lunch_start_time": settings_obj.lunch_start_time,
        "lunch_end_time": settings_obj.lunch_end_time,

        "slot_duration": settings_obj.slot_duration,
        "week_holiday": settings_obj.week_holiday
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwner])
def save_settings(request):
    data = request.data

    settings_obj = BarberShopSettings.objects.first()

    if settings_obj:
        settings_obj.opening_time = data.get('opening_time')
        settings_obj.closing_time = data.get('closing_time')

        settings_obj.lunch_start_time = data.get('lunch_start_time')
        settings_obj.lunch_end_time = data.get('lunch_end_time')

        settings_obj.slot_duration = data.get('slot_duration')
        settings_obj.week_holiday = data.get('week_holiday')

        settings_obj.save()
    else:
        settings_obj = BarberShopSettings.objects.create(
            opening_time = data.get('opening_time'),
            closing_time = data.get('closing_time'),

            lunch_start_time = data.get('lunch_start_time'),
            lunch_end_time = data.get('lunch_end_time'),

            slot_duration = data.get('slot_duration'),
            week_holiday = data.get('week_holiday')
        )
    return Response({'message' : 'Settings saved successfully!!!'})