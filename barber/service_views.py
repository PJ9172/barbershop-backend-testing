import traceback
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import *
from rest_framework.response import Response
from .models import *

# Create your views here.



# Get all services & categories
@api_view(['GET'])
def get_services(request):

    try:
        categories = Category.objects.all()
        response = []

        for category in categories:
            services = Service.objects.filter(
                category=category,
                is_active=True
            )

            service_data = [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "cost": s.cost,
                    "duration": s.duration
                }
                for s in services
            ]

            response.append({
                "id": category.id,
                "name": category.name,
                "services": service_data
            })

        return Response(response)

    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)



#  Add category
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def add_category(request):

    try:
        name = request.data.get("name")
        if not name:
            return Response({
                "error": "Category name required"
            }, status=400)

        exists = Category.objects.filter(
            name__iexact=name
        ).exists()

        if exists:
            return Response({
                "error": "Category already exists"
            }, status=400)

        category = Category.objects.create(
            name=name
        )

        return Response({
            "message": "Category added successfully",
            "id": category.id
        })

    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)


#  Add Service
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def add_service(request):

    try:
        data = request.data

        category = Category.objects.filter(
            id=data.get("category_id")
        ).first()

        if not category:
            return Response({
                "error": "Category not found"
            }, status=404)

        Service.objects.create(
            category=category,
            name=data.get("name"),
            description=data.get("description"),
            cost=data.get("cost"),
            duration=data.get("duration")
        )

        return Response({
            "message": "Service added successfully"
        })

    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)


#  Update Service
@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def update_service(request, id):

    try:
        service = Service.objects.filter(
            id=id
        ).first()

        if not service:
            return Response({
                "error": "Service not found"
            }, status=404)

        service.name = request.data.get(
            "name",
            service.name
        )

        service.description = request.data.get(
            "description",
            service.description
        )

        service.cost = request.data.get(
            "cost",
            service.cost
        )

        service.duration = request.data.get(
            "duration",
            service.duration
        )

        service.save()
        return Response({
            "message": "Service updated successfully"
        })

    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)



# Delete Category
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def delete_category(request, id):

    try:
        category = Category.objects.filter(
            id=id
        ).first()

        if not category:
            return Response({
                "error": "Category not found"
            }, status=404)

        category.delete()

        return Response({
            "message": "Category deleted successfully"
        })

    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)


#  Delete Service
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def delete_service(request, id):

    try:
        service = Service.objects.filter(
            id=id
        ).first()

        if not service:
            return Response({
                "error": "Service not found"
            }, status=404)

        service.delete()

        return Response({
            "message": "Service deleted successfully"
        })

    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)