from django.urls import path
from .settings_views import *

urlpatterns = [
    path('/', get_settings),
    path('save/', save_settings),
]