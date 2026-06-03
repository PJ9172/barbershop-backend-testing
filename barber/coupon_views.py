from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import *
from rest_framework.response import Response
from .models import *
import traceback


# Create coupon
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def create_coupon(request):

    try:
        code = request.data.get("code")
        discount_type = request.data.get("discount_type")
        discount_value = request.data.get("discount_value")
        minimum_order_value = request.data.get("minimum_order_value", 0.00)
        valid_till = request.data.get("valid_till")
        is_active = request.data.get("is_active", True)

        if not all([code, discount_type, discount_value, valid_till, is_active]):
            return Response(
                {"error": "All fields are required"},
                status=400
            )

        if Coupon.objects.filter(code=code).exists():
            return Response(
                {"error": "Coupon code already exists"},
                status=400
            )

        coupon = Coupon.objects.create(
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            min_order_value=minimum_order_value,
            valid_till=valid_till,
            is_active=is_active
        )

        return Response({
            "message": "Coupon created successfully",
            "coupon": {
                "id": coupon.id,
                "code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "minimum_order_value": coupon.min_order_value,
                "valid_till": coupon.valid_till,
                "is_active": coupon.is_active
            }
        })
    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)
    

# Get coupons list
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def get_coupons_list(request):

    try:
        coupons = Coupon.objects.all().order_by("-created_at")

        coupons_data = [
            {
                "id": coupon.id,
                "code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "minimum_order_value": coupon.min_order_value,
                "valid_till": coupon.valid_till,
                "is_active": coupon.is_active
            }
            for coupon in coupons
        ]

        return Response({
            "coupons": coupons_data
        })
    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)
    

# Activate/Deactivate coupon
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def update_coupon(request, coupon_id):

    try:
        action = request.data.get("action")

        if action not in ["active", "inactive"]:
            return Response(
                {"error": "Invalid action"},
                status=400
            )

        try:
            coupon = Coupon.objects.get(id=coupon_id)
        except Coupon.DoesNotExist:
            return Response(
                {"error": "Coupon not found"},
                status=404
            )

        coupon.is_active = True if action == "active" else False
        coupon.save()

        return Response({
            "message": f"Coupon {'activated' if coupon.is_active else 'deactivated'} successfully",
            "coupon": {
                "id": coupon.id,
                "code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "minimum_order_value": coupon.min_order_value,
                "valid_till": coupon.valid_till,
                "is_active": coupon.is_active
            }
        })
    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)
    