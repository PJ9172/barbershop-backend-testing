from django.urls import path

from .bookings_views import *

urlpatterns = [
    path('get-available-slots/', get_available_slots),
    path('get-available-dates/', get_available_dates),
    path('add-online-booking/', create_online_booking),
    path('add-offline-booking/', create_offline_booking),
    path('get-owner-bookings/', get_owner_bookings_list),
    path('get-customer-bookings/', get_customer_bookings_list),
    path('home-dashboard/', home_dashboard),
    path('owner-update-booking-status/<int:booking_id>/', update_booking_status_by_owner),
    path('customer-cancel-booking-status/<int:booking_id>/', cancel_booking_by_customer),
]