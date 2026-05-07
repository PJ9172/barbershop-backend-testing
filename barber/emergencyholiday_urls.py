from django.urls import path
from .emergencyholiday_views import *

urlpatterns = [
    path('', get_holidays),
    path('add/', add_holidays),
]