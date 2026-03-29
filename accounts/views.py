from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
import requests
from rest_framework import status
from .models import User, Role
from .otp_service import generate_otp, save_otp, validate_otp
from .utils import send_otp


# send-otp api
@api_view(['POST'])
def send_register_otp(request):
    mobile = request.data.get("mobile_no")

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
        "role_name": request.user.role.name if request.user.role else None
    })