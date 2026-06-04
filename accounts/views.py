from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import *
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from .models import User, Role
from django.db.models import Sum
from .otp_service import generate_otp, save_otp, validate_otp
from .utils import send_otp
from barber.models import (
    Booking,
    EmergencyHoliday
)
import traceback


# send-otp api
@api_view(['POST'])
def send_register_otp(request):
    mobile = request.data.get("mobile_no")

    if User.objects.filter(mobile_no=mobile).exists():
        return Response({"error": "User already exists"}, status=400)

    if not mobile:
        return Response({"error": "Mobile number required"}, status=400)

    otp = generate_otp()
    # print("otp : ",otp)
    save_otp(mobile, otp)

    response = send_otp(mobile, otp)
    print("OTP:", otp)
    print("SMS RESPONSE:", response)

    return Response({"message": "OTP sent"})


#  register user api
@api_view(['POST'])
def register_user(request):
    data = request.data

    if User.objects.filter(mobile_no=data["mobile_no"]).exists():
        return Response({"error": "User already exists"}, status=400)

    if data["password"] != data["confirm_password"]:
        return Response({"error": "Passwords do not match"}, status=400)

    if not validate_otp(data["mobile_no"], data["otp"]):
        return Response({"error": "Invalid OTP"}, status=400)

    role = Role.objects.get(id=3)  # default user

    user = User.objects.create_user(
        mobile_no=data["mobile_no"],
        password=data["password"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        role=role
    )

    return Response({"message": "User registered successfully"})


# Login API JWT

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate


@api_view(['POST'])
def login_user(request):
    mobile = request.data.get("mobile_no")
    password = request.data.get("password")

    user = authenticate(mobile_no=mobile, password=password)

    if not user:
        return Response({"error": "Invalid credentials"}, status=401)

    refresh = RefreshToken.for_user(user)

    role_name = user.role.name if user.role else None

    return Response({
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
        "role_name": role_name
    })


# refresh_token api
@api_view(['POST'])
def refresh_token(request):
    refresh_token = request.data.get("refresh_token")

    if not refresh_token:
        return Response({"error": "Refresh token required"}, status=400)

    try:
        refresh = RefreshToken(refresh_token)
        return Response({
            "access_token": str(refresh.access_token)
        })
    except Exception:
        return Response({"error": "Invalid refresh token"}, status=401)
    

#  profile api
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    return Response({
        "mobile_no": request.user.mobile_no,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "date_joined": request.user.date_joined,
        "role_id": request.user.role.id if request.user.role else None,
        "role_name": request.user.role.name if request.user.role else None,
        "shop_name": request.user.shop_name if request.user.shop_name else None
    })


#  send-reset-otp

@api_view(['POST'])
def send_reset_otp(request):
    mobile = request.data.get("mobile_no")

    if not mobile:
        return Response({"error": "Mobile number required"}, status=400)

    user = User.objects.filter(mobile_no=mobile).first()
    if not user:
        return Response({"error": "User not found"}, status=404)

    otp = generate_otp()
    save_otp(mobile, otp)

    # send SMS
    send_otp(mobile, otp)

    print("RESET OTP:", otp)  # for testing

    return Response({"message": "OTP sent for password reset"})


#  reset-password

@api_view(['POST'])
def reset_password(request):
    mobile = request.data.get("mobile_no")
    otp = request.data.get("otp")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")

    if new_password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=400)

    if not validate_otp(mobile, otp):
        return Response({"error": "Invalid or expired OTP"}, status=400)

    user = User.objects.filter(mobile_no=mobile).first()
    if not user:
        return Response({"error": "User not found"}, status=404)

    user.set_password(new_password)
    user.save()

    return Response({"message": "Password reset successful"})



# get owner's profile tab - used by owner and admin to view owner details and analytics
@api_view(['GET'])
@permission_classes([
    IsAuthenticated,
    IsOwnerOrAdmin
])
def get_owner_profile(request):

    try:

        user = request.user

        total_income = (
            Booking.objects.filter(
                status="completed"
            ).aggregate(
                total=Sum("total_amount")
            )["total"] or 0
        )

        total_bookings = Booking.objects.filter(
            status="completed"
        ).count()

        holidays = EmergencyHoliday.objects.all().order_by(
            "-created_at"
        )[:5]

        holiday_data = []

        for holiday in holidays:

            holiday_data.append({

                "id":
                    holiday.id,

                "start_date":
                    holiday.start_date,

                "end_date":
                    holiday.end_date,

                "reason":
                    holiday.reason
            })

        return Response({

            "user": {

                "id":
                    user.id,

                "first_name":
                    user.first_name,

                "last_name":
                    user.last_name,

                "mobile_no":
                    user.mobile_no,

                "email":
                    user.email,

                "role":
                    user.role.name
            },

            "analytics": {

                "total_income":
                    total_income,

                "total_bookings":
                    total_bookings
            },

            "emergency_holidays":
                holiday_data
        })

    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)
    


# get customer profile tab - used by customer only to view customer details and analytics
@api_view(['GET'])
@permission_classes([
    IsAuthenticated,
    IsCustomer
])
def get_customer_profile(request):

    try:

        user = request.user

        total_bookings = Booking.objects.filter(
            user_id=user.id
        ).count()

        completed_bookings = Booking.objects.filter(
            user_id=user.id,
            status="completed"
        ).count()

        cancelled_bookings = Booking.objects.filter(
            user_id=user.id,
            status="cancelled"
        ).count()

        booked_bookings = Booking.objects.filter(
            user_id=user.id,
            status="booked"
        ).count()

        return Response({

            "user": {

                "id":
                    user.id,

                "first_name":
                    user.first_name,

                "last_name":
                    user.last_name,

                "mobile_no":
                    user.mobile_no,

                "email":
                    user.email,

                "role":
                    user.role.name
            },

            "analytics": {

                "total_bookings":
                    total_bookings,

                "completed_bookings":
                    completed_bookings,

                "cancelled_bookings":
                    cancelled_bookings,

                "booked_bookings":
                    booked_bookings
            }
        })

    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)