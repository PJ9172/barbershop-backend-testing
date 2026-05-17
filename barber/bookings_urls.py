from django.urls import path

from .bookings_views import *

urlpatterns = [
    path('available-slots/', get_available_slots),
    path('available-dates/', get_available_dates),
    path('add/', create_booking),
    path('owner-bookings/', owner_bookings_list)
]