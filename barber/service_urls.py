from django.urls import path
from .service_views import *

urlpatterns = [
    path('', get_services),
    
    path('categories/add/', add_category),
    path('categories/delete/<int:id>/', delete_category),

    path('add/', add_service),
    path('update/<int:id>/', update_service),
    path('delete/<int:id>/', delete_service),
]