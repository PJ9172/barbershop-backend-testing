from django.urls import path
from .views import *

urlpatterns = [
    path('send-otp/', send_register_otp),
    path('register/', register_user),
    path('login/', login_user),
    path('refresh/', refresh_token),
    path('profile/', user_profile),
]