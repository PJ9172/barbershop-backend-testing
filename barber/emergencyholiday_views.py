from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import *
from rest_framework.response import Response
from .models import *

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def get_holidays(request):
    holidays = EmergencyHoliday.objects.all().order_by("holiday_date")

    data = [
        {
            "id": h.id,
            "holiday_date": h.holiday_date,
            "reason": h.reason
        }
        for h in holidays
    ]

    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def add_holidays(request):
    data = request.data
    date = data.get('holiday_date')
    if EmergencyHoliday.objects.filter(holiday_date=date).first():
        return Response({
            'message' : 'This date already exits!!'
        })
    
    EmergencyHoliday.objects.create(
        holiday_date = date,
        reason = data.get('reason')
    )
    return Response({'message' : 'Emergency holiday added!!!'})