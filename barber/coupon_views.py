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
        traceback.print_exc()
        return Response(
            {"error": "An error occurred while creating the coupon"},
            status=500
        )
