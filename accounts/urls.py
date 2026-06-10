from django.urls import path
from .views import *

urlpatterns = [
    path('send-otp/', send_register_otp),
    path('register/', register_user),
    path('login/', login_user),
    path('refresh/', refresh_token),
    path('profile/', user_profile),
    path('update-profile/', update_profile),
    path('send-reset-otp/', send_reset_otp),
    path('reset-password/', reset_password),
    path('get-owner-profile/', get_owner_profile),
    path('get-customer-profile/', get_customer_profile),
]