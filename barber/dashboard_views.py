from datetime import datetime, date, timedelta
import traceback
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Booking, BarberShopSettings, EmergencyHoliday
from accounts.permissions import IsOwnerOrAdmin
from django.db.models import Sum

# Get owner-dashboard
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def owner_dashboard(request):

    try:

        selected_date_str = request.GET.get(
            "selected_date"
        )

        selected_date = (
            datetime.strptime(
                selected_date_str,
                "%Y-%m-%d"
            ).date()

            if selected_date_str
            else date.today()
        )

        today = date.today()

        # -----------------------------------
        # TODAY'S overview
        # -----------------------------------

        today_bookings = Booking.objects.filter(
            booking_date=today
        )

        today_overview = {
            "total_appointments": today_bookings.count(),

            "completed": today_bookings.filter(
                status="completed"
            ).count(),

            "pending": today_bookings.filter(
                status="booked"
            ).count(),

            "cancelled": today_bookings.filter(
                status="cancelled"
            ).count(),

            "revenue":
                today_bookings.filter(
                    status="completed"
                ).aggregate(
                    total=Sum("total_amount")
                )["total"] or 0
        }

        # -----------------------------------
        # CURRENT WEEK overview
        # -----------------------------------

        start_of_week = (
            today -
            timedelta(days=today.weekday())
        )

        week_bookings = Booking.objects.filter(
            booking_date__range=[
                start_of_week,
                start_of_week + timedelta(days=6)
            ]
        )

        settings_obj = BarberShopSettings.objects.first()

        week_data = []

        for i in range(7):

            current_date = (
                start_of_week +
                timedelta(days=i)
            )

            booking_count = Booking.objects.filter(
                booking_date=current_date,
                status="booked"
            ).count()

            weekday_name = current_date.strftime("%a")

            is_weekly_holiday = False

            if (
                settings_obj and
                settings_obj.week_holiday
            ):

                is_weekly_holiday = (
                    weekday_name.lower() ==
                    settings_obj.week_holiday.lower()
                )

            is_emergency_holiday = (
                EmergencyHoliday.objects.filter(
                    enabled=True,
                    start_date__lte=current_date,
                    end_date__gte=current_date
                ).exists()
            )

            week_data.append({

                "date":
                    current_date.strftime("%Y-%m-%d"),

                "day":
                    current_date.strftime("%a"),

                "booking_count":
                    booking_count,

                "is_weekly_holiday":
                    is_weekly_holiday,

                "is_emergency_holiday":
                    is_emergency_holiday
            })


        week_overview = {
            "start_date":
                start_of_week.strftime("%Y-%m-%d"),

            "end_date":
                (
                    start_of_week +
                    timedelta(days=6)
                ).strftime("%Y-%m-%d"),

            "total_bookings":
                week_bookings.count(),

            "completed":
                week_bookings.filter(
                    status="completed"
                ).count(),

            "pending":
                week_bookings.filter(
                    status="booked"
                ).count(),

            "cancelled":
                week_bookings.filter(
                    status="cancelled"
                ).count(),

            "total_revenue":
                week_bookings.filter(
                    status="completed"
                ).aggregate(
                    total=Sum("total_amount")
                )["total"] or 0,

            "chart":
                week_data
        }
        

        ################################
        # CURRENT MONTH overview
        ################################
        month_bookings = Booking.objects.filter(
            booking_date__month=today.month,
            booking_date__year=today.year
        )

        month_overview = {

            "month":
                today.strftime("%B"),

            "year":
                today.year,

            "total_bookings":
                month_bookings.count(),

            "completed":
                month_bookings.filter(
                    status="completed"
                ).count(),

            "pending":
                month_bookings.filter(
                    status="booked"
                ).count(),

            "cancelled":
                month_bookings.filter(
                    status="cancelled"
                ).count(),

            "total_revenue":
                month_bookings.filter(
                    status="completed"
                ).aggregate(
                    total=Sum("total_amount")
                )["total"] or 0
        }

        # -----------------------------------
        # APPOINTMENTS
        # -----------------------------------

        selected_bookings = Booking.objects.filter(
            booking_date=selected_date
        ).order_by("start_time")

        appointments = []

        for booking in selected_bookings:

            services = booking.services.all()

            appointments.append({

                "booking_id":
                    booking.id,

                "customer_name": (
                    f"{booking.user.first_name} {booking.user.last_name}"
                    if booking.user
                    else booking.customer_name
                ),

                "services":
                    [s.name for s in services],

                "start_time":
                    booking.start_time.strftime(
                        "%I:%M %p"
                    ),

                "end_time":
                    booking.end_time.strftime(
                        "%I:%M %p"
                    ),

                "status":
                    booking.status,

                "total_amount":
                    booking.total_amount
            })

        # -----------------------------------
        # FINAL RESPONSE
        # -----------------------------------

        return Response({

            "first_name":
                request.user.first_name,

            "today": {
                "date":
                    today.strftime("%Y-%m-%d"),

                "overview":
                    today_overview
            },

            "this_week_overview":
                week_overview,

            "this_month_overview":
                month_overview,

            "appointments":
                appointments
        })
    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)
    
