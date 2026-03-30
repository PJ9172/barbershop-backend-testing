from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import *
from rest_framework.response import Response
from .models import *

# Create your views here.

# Get all services
@api_view(['GET'])
def get_services(request):
    services = Service.objects.filter(is_active=True)
    
    data = [
        {
            "id": s.id,
            "name": s.name,
            "cost": s.cost,
            "duration": s.duration
        }
        for s in services
    ]

    return Response(data)


#  Add service

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def add_service(request):
    data = request.data

    service = Service.objects.create(
        name=data.get("name"),
        description=data.get("description"),
        cost=data.get("cost"),
        duration=data.get("duration")
    )

    return Response({"message": "Service added"})


#  Update Service

@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def update_service(request, id):
    service = Service.objects.filter(id=id).first()

    if not service:
        return Response({"error": "Service not found"}, status=404)

    service.name = request.data.get("name", service.name)
    service.cost = request.data.get("cost", service.cost)
    service.duration = request.data.get("duration", service.duration)

    service.save()

    return Response({"message": "Service updated"})


#  Delete Service

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def delete_service(request, id):
    service = Service.objects.filter(id=id).first()

    if not service:
        return Response({"error": "Service not found"}, status=404)

    service.is_active = False
    service.save()

    return Response({"message": "Service deleted"})