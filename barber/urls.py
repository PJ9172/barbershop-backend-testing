from django.urls import path
from .views import *

urlpatterns = [
    path('', get_services),
    path('add/', add_service),
    path('update/<int:id>/', update_service),
    path('delete/<int:id>/', delete_service),
]