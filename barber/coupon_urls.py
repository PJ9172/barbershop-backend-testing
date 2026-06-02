from django.urls import path

from .coupon_views import *

urlpatterns = [
    path('add-coupon/', create_coupon),
    path('get-coupons/', get_coupons_list),
    path('active-coupon/<int:coupon_id>/', update_coupon),
    path('inactive-coupon/<int:coupon_id>/', update_coupon),
]