from django.urls import path
from .settings_views import *
from .emergencyholiday_views import *

urlpatterns = [
    path('', get_settings),
    path('save/', save_settings),
    path('emergency-holiday/', get_emergency_holiday),
    path('emergency-holiday/<id>/', delete_emergency_holiday)

]