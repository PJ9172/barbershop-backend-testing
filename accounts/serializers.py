import random
import requests
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Role, OTP


class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    mobile_no = serializers.CharField(max_length=15)
    role_id = serializers.IntegerField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_mobile_no(self, value):
        if User.objects.filter(mobile_no=value).exists():
            raise serializers.ValidationError("A user with this mobile number already exists.")
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError("Enter a valid 10-digit mobile number.")
        return value

    def validate_role_id(self, value):
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid role_id. Use 1 (superadmin), 2 (owner), or 3 (user).")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        role_id = validated_data.pop('role_id')
        role = Role.objects.get(id=role_id)
        user = User.objects.create_user(
            mobile_no=validated_data['mobile_no'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=role,
        )
        return user


class LoginSerializer(serializers.Serializer):
    mobile_no = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            request=self.context.get('request'),
            username=data['mobile_no'],
            password=data['password'],
        )
        if user is None:
            raise serializers.ValidationError("Invalid mobile number or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account is deactivated.")
        data['user'] = user
        return data

    def send_otp(self, mobile_no):
        """Generate OTP, save to DB, and send via Fast2SMS"""
        otp_code = str(random.randint(100000, 999999))

        # Save OTP to database
        otp_obj = OTP.objects.create(mobile_no=mobile_no, otp=otp_code)

        # Send OTP via Fast2SMS
        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": settings.FAST2SMS_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {
            "route": "otp",
            "variables_values": otp_code,
            "numbers": mobile_no,
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise serializers.ValidationError(f"Failed to send OTP: {str(e)}")

        return str(otp_obj.request_id)


class VerifyOTPSerializer(serializers.Serializer):
    mobile_no = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        try:
            otp_obj = OTP.objects.filter(
                mobile_no=data['mobile_no'],
                is_verified=False,
            ).latest('created_at')
        except OTP.DoesNotExist:
            raise serializers.ValidationError("No OTP found for this mobile number. Please login again.")

        if otp_obj.is_expired():
            raise serializers.ValidationError("OTP has expired. Please login again to get a new OTP.")

        if otp_obj.otp != data['otp']:
            raise serializers.ValidationError("Invalid OTP.")

        # Mark OTP as verified
        otp_obj.is_verified = True
        otp_obj.save()

        # Get the user and generate JWT tokens
        try:
            user = User.objects.get(mobile_no=data['mobile_no'])
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        refresh = RefreshToken.for_user(user)
        data['tokens'] = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        data['user'] = user
        return data
