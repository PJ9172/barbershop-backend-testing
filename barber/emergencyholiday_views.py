from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import *
from rest_framework.response import Response
from .models import *


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def get_emergency_holiday(request):
    emergencies = EmergencyHoliday.objects.filter(
        enabled=True
    ).order_by('-created_at')

    data = [
        {
            "id": emergency.id,
            "enabled": emergency.enabled,
            "start_date": emergency.start_date,
            "end_date": emergency.end_date,
            "total_days": emergency.total_days,
            "reason": emergency.reason,
            "created_date" : emergency.created_at,
        }
        for emergency in emergencies
    ]

    return Response({
        "emergency_holiday": data
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def delete_emergency_holiday(request, id):

    holiday = EmergencyHoliday.objects.filter(id=id).first()

    if not holiday:
        return Response(
            {"error": "Holiday not found"},
            status=404
        )

    holiday.delete()

    return Response({
        "message": "Holiday deleted successfully"
    })