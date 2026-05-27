from datetime import datetime, timedelta, date

from django.db import transaction

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import *
from rest_framework.response import Response

from .models import (
    BarberShopSettings,
    EmergencyHoliday,
    Booking,
    Service
)


import traceback


# Get available dates for booking
@api_view(['GET'])
def get_available_dates(request):

    try:

        settings_obj = BarberShopSettings.objects.first()

        if not settings_obj:
            return Response({
                "error": "Shop settings not configured"
            }, status=400)

        available_dates = []

        current_date = date.today()

        while len(available_dates) < 7:

            # -----------------------------------
            # WEEKLY HOLIDAY CHECK
            # -----------------------------------

            weekday_name = current_date.strftime("%a")

            is_weekly_holiday = (
                settings_obj.weekly_holiday and
                weekday_name.lower() ==
                settings_obj.weekly_holiday.lower()
            )

            # -----------------------------------
            # EMERGENCY HOLIDAY CHECK
            # -----------------------------------

            is_emergency_holiday = EmergencyHoliday.objects.filter(
                enabled=True,
                start_date__lte=current_date,
                end_date__gte=current_date
            ).exists()

            # -----------------------------------
            # ADD AVAILABLE DATE
            # -----------------------------------

            if (
                not is_weekly_holiday and
                not is_emergency_holiday
            ):

                available_dates.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "day": current_date.strftime("%a"),
                    "is_today": current_date == date.today()
                })

            current_date += timedelta(days=1)

        return Response(available_dates)

    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)
    


# Get available slots for a specific date
@api_view(['GET'])
def get_available_slots(request):

    try:

        date_str = request.GET.get("date")
        service_ids_str = request.GET.get("service_ids")

        if not date_str:
            return Response({
                "error": "date is required"
            }, status=400)

        if not service_ids_str:
            return Response({
                "error": "service_ids required"
            }, status=400)

        booking_date = datetime.strptime(
            date_str,
            "%Y-%m-%d"
        ).date()

        service_ids = [
            int(x)
            for x in service_ids_str.split(",")
        ]

        services = Service.objects.filter(
            id__in=service_ids,
            is_active=True
        )

        if not services.exists():
            return Response({
                "error": "Invalid services"
            }, status=400)

        # -----------------------------------
        # TOTAL DURATION
        # -----------------------------------

        total_duration = sum(
            s.duration for s in services
        )

        # -----------------------------------
        # SETTINGS
        # -----------------------------------

        settings_obj = BarberShopSettings.objects.first()

        if not settings_obj:
            return Response({
                "error": "Shop settings missing"
            }, status=400)

        # -----------------------------------
        # WEEKLY HOLIDAY
        # -----------------------------------

        weekday_name = booking_date.strftime("%a")

        if (
            settings_obj.weekly_holiday and
            weekday_name.lower() ==
            settings_obj.weekly_holiday.lower()
        ):
            return Response({
                "holiday": True,
                "message": "Weekly holiday"
            })

        # -----------------------------------
        # EMERGENCY HOLIDAY
        # -----------------------------------

        emergency = EmergencyHoliday.objects.filter(
            enabled=True,
            start_date__lte=booking_date,
            end_date__gte=booking_date
        ).exists()

        if emergency:
            return Response({
                "holiday": True,
                "message": "Emergency holiday"
            })

        # -----------------------------------
        # SLOT GENERATION
        # -----------------------------------

        available_slots = []

        slot_duration = settings_obj.slot_duration

        current_datetime = datetime.combine(
            booking_date,
            settings_obj.opening_time
        )

        closing_datetime = datetime.combine(
            booking_date,
            settings_obj.closing_time
        )

        lunch_start = (
            datetime.combine(
                booking_date,
                settings_obj.lunch_start_time
            )
            if settings_obj.lunch_start_time
            else None
        )

        lunch_end = (
            datetime.combine(
                booking_date,
                settings_obj.lunch_end_time
            )
            if settings_obj.lunch_end_time
            else None
        )

        now = datetime.now()

        while current_datetime < closing_datetime:

            booking_end = (
                current_datetime +
                timedelta(minutes=total_duration)
            )

            # -----------------------------------
            # CANNOT EXCEED CLOSING TIME
            # -----------------------------------

            if booking_end > closing_datetime:
                break

            # -----------------------------------
            # PAST TIME SKIP
            # -----------------------------------

            if (
                booking_date == now.date() and
                current_datetime <= now
            ):
                current_datetime += timedelta(
                    minutes=slot_duration
                )
                continue

            # -----------------------------------
            # LUNCH OVERLAP CHECK
            # -----------------------------------

            overlaps_lunch = False

            if lunch_start and lunch_end:

                overlaps_lunch = (
                    current_datetime < lunch_end and
                    booking_end > lunch_start
                )

            if overlaps_lunch:
                current_datetime += timedelta(
                    minutes=slot_duration
                )
                continue

            # -----------------------------------
            # OVERLAP CHECK
            # -----------------------------------

            overlapping_bookings = Booking.objects.filter(
                booking_date=booking_date,
                status="booked"
            )

            conflict_count = 0

            for booking in overlapping_bookings:

                existing_start = datetime.combine(
                    booking_date,
                    booking.start_time
                )

                existing_end = datetime.combine(
                    booking_date,
                    booking.end_time
                )

                overlaps = (
                    current_datetime < existing_end and
                    booking_end > existing_start
                )

                if overlaps:
                    conflict_count += 1

            is_available = (
                conflict_count <
                settings_obj.slot_capacity
            )

            available_slots.append({
                "start_time":
                    current_datetime.strftime(
                        "%I:%M %p"
                    ),

                "end_time":
                    booking_end.strftime(
                        "%I:%M %p"
                    ),

                "available": is_available,

                "conflict_count": conflict_count
            })

            current_datetime += timedelta(
                minutes=slot_duration
            )

        return Response({
            "total_duration": total_duration,
            "slots": available_slots
        })

    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)
    

    
# Helper function to save booking (used by both online and offline booking creation)
def save_booking(request, booking_type="online"):
    try:

        data = request.data

        booking_date = datetime.strptime(
            data.get("booking_date"),
            "%Y-%m-%d"
        ).date()

        start_time = datetime.strptime(
            data.get("start_time"),
            "%I:%M %p"
        ).time()

        service_ids = data.get("service_ids", [])

        services = Service.objects.filter(
            id__in=service_ids,
            is_active=True
        )

        if not services.exists():
            return Response({
                "error": "Invalid services"
            }, status=400)
        
        if len(service_ids) != services.count():
            return Response({
                "error": "Some services are invalid"
            }, status=400)

        # -----------------------------------
        # CALCULATE TOTALS
        # -----------------------------------

        total_duration = sum(
            s.duration for s in services
        )

        total_amount = sum(
            s.cost for s in services
        )

        # -----------------------------------
        # VALIDATE START TIME
        # -----------------------------------

        settings_obj = BarberShopSettings.objects.first()
        if not settings_obj:
            return Response({
                "error": "Shop settings missing"
            }, status=400)
        
        if start_time < settings_obj.opening_time:
            return Response({
                "error": "Booking cannot start before opening time"
            }, status=400)

        # -----------------------------------
        # CALCULATE END TIME
        # -----------------------------------

        start_datetime = datetime.combine(
            booking_date,
            start_time
        )

        end_datetime = (
            start_datetime +
            timedelta(minutes=total_duration)
        )

        end_time = end_datetime.time()

        if end_time > settings_obj.closing_time:
            return Response({
                "error": "Booking cannot end after closing time"
            }, status=400)

        # -----------------------------------
        # OVERLAP CHECK
        # -----------------------------------
        if (
            settings_obj.lunch_start_time and
            settings_obj.lunch_end_time
        ):

            lunch_start = datetime.combine(
                booking_date,
                settings_obj.lunch_start_time
            )

            lunch_end = datetime.combine(
                booking_date,
                settings_obj.lunch_end_time
            )

            overlaps_lunch = (
                start_datetime < lunch_end and
                end_datetime > lunch_start
            )

            if overlaps_lunch:
                return Response({
                    "error": "Slot overlaps lunch time"
                }, status=400)

        # -----------------------------------
        # OVERLAP CHECK
        # -----------------------------------

        overlapping = Booking.objects.filter(
            booking_date=booking_date,
            status="booked"
        )

        conflict_count = 0

        for booking in overlapping:

            existing_start = datetime.combine(
                booking_date,
                booking.start_time
            )

            existing_end = datetime.combine(
                booking_date,
                booking.end_time
            )

            overlaps = (
                start_datetime < existing_end and
                end_datetime > existing_start
            )

            if overlaps:
                conflict_count += 1


        if (
            conflict_count >=
            settings_obj.slot_capacity
        ):
            return Response({
                "error": "Selected slot not available"
            }, status=400)

        # -----------------------------------
        # CREATE BOOKING
        # -----------------------------------

        if booking_type == "offline":
            if not data.get("customer_name"):
                return Response({
                    "error": "customer_name is required for offline booking"
                }, status=400)

            if not data.get("customer_mobile_no"):
                return Response({
                    "error": "customer_mobile_no is required for offline booking"
                }, status=400)
            
            customer_name = data.get("customer_name")
            customer_mobile_no = data.get("customer_mobile_no")
            customer_email = data.get("customer_email", None)

        with transaction.atomic():

            booking = Booking.objects.create(
                user=request.user if booking_type == "online" else None,

                customer_name=(
                    customer_name if booking_type == "offline"
                    else (
                        f"{request.user.first_name} "f"{request.user.last_name}"
                    ).strip()
                ),
                customer_mobile_no=(
                    customer_mobile_no 
                    if booking_type == "offline" 
                    else request.user.mobile_no
                ),
                customer_email=(
                    customer_email 
                    if booking_type == "offline" 
                    else (request.user.email if request.user.email else None)
                ),

                booking_date=booking_date,
                booking_type=booking_type,

                start_time=start_time,
                end_time=end_time,

                total_duration=total_duration,
                total_amount=total_amount,

                created_by=request.user.role.name
            )

            booking.services.set(services)

        return Response({
            "message": "Booking created successfully",

            "booking_id": booking.id,

            "total_duration": total_duration,

            "total_amount": total_amount
        })

    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)


# Save a new online booking
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_online_booking(request):
    try:
        return save_booking(request, booking_type="online")
    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)
    

# save a new offline booking
@api_view(['POST'])
@permission_classes([IsOwnerOrAdmin])
def create_offline_booking(request):
    try:
        return save_booking(request, booking_type="offline")
    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)


# Get bookings list (future, past, today)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def get_owner_bookings_list(request):

    try:

        booking_type = request.GET.get("type")

        selected_date_str = request.GET.get("date")

        today = date.today()

        bookings = Booking.objects.all()

        # -----------------------------------
        # TODAY BOOKINGS
        # -----------------------------------

        if booking_type == "today":

            bookings = bookings.filter(
                booking_date=today
            )

        # -----------------------------------
        # FUTURE BOOKINGS
        # -----------------------------------

        elif booking_type == "future":

            bookings = bookings.filter(
                booking_date__gt=today
            )

        # -----------------------------------
        # PAST BOOKINGS
        # -----------------------------------

        elif booking_type == "past" or booking_type == None:

            if not selected_date_str:

                return Response({
                    "error": "date query param required"
                }, status=400)

            selected_date = datetime.strptime(
                selected_date_str,
                "%Y-%m-%d"
            ).date()

            bookings = bookings.filter(
                booking_date=selected_date
            )

        else:

            return Response({
                "error": "Invalid type"
            }, status=400)

        # -----------------------------------
        # SORTING
        # -----------------------------------

        bookings = bookings.order_by(
            "-booking_date",
            "start_time"
        )

        response = []

        for booking in bookings:

            services = booking.services.all()

            service_names = [
                s.name for s in services
            ]

            response.append({

                "booking_id": booking.id,

                "customer_name":
                    f"{booking.user.first_name} " if booking.user else f"{booking.customer_name}" +
                    f"{booking.user.last_name}" if booking.user else "",

                "mobile_no":
                    booking.user.mobile_no if booking.user else booking.customer_mobile_no,

                "booking_date":
                    booking.booking_date.strftime(
                        "%Y-%m-%d"
                    ),

                "start_time":
                    booking.start_time.strftime(
                        "%I:%M %p"
                    ),

                "end_time":
                    booking.end_time.strftime(
                        "%I:%M %p"
                    ),

                "total_amount":
                    booking.total_amount,

                "total_duration":
                    booking.total_duration,

                "status":
                    booking.status,

                "services":
                    service_names
            })

        return Response(response)

    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)
    

# Get customer's bookings list (booked, completed, cancelled)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_customer_bookings_list(request):

    try:

        status_filter = request.GET.get("status")

        bookings = Booking.objects.filter(
            user=request.user
        ).order_by("-booking_date", "-start_time")

        if status_filter in ["booked", "completed", "cancelled"]:
            bookings = bookings.filter(
                status=status_filter
            )
        elif not status_filter:
            pass
        else:
            return Response({
                "error": "Invalid type"
            }, status=400)

        response = []

        for booking in bookings:

            services = booking.services.all()

            service_data = [
                {
                    "id": s.id,
                    "name": s.name
                }
                for s in services
            ]

            response.append({

                "booking_id": booking.id,

                "booking_date":
                    booking.booking_date.strftime(
                        "%Y-%m-%d"
                    ),

                "start_time":
                    booking.start_time.strftime(
                        "%I:%M %p"
                    ),

                "end_time":
                    booking.end_time.strftime(
                        "%I:%M %p"
                    ),

                "status": booking.status,

                "total_duration":
                    booking.total_duration,

                "total_amount":
                    booking.total_amount,

                "services": service_data
            })

        return Response(response)

    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)
    

# Get home-dashboard
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOwnerOrAdmin])
def home_dashboard(request):

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
        # TOTAL BOOKINGS
        # -----------------------------------

        total_bookings = Booking.objects.count()

        # -----------------------------------
        # CURRENT WEEK
        # -----------------------------------

        start_of_week = (
            today -
            timedelta(days=today.weekday())
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

        total_week_bookings = sum(
            item["booking_count"]
            for item in week_data
        )

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

                "customer_name":
                    f"{booking.user.first_name} " if booking.user else f"{booking.customer_name}" +
                    f"{booking.user.last_name}" if booking.user else "",

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

            "total_bookings":
                total_bookings,

            "total_week_bookings":
                total_week_bookings,

            "week_data":
                week_data,

            "appointments":
                appointments
        })

    except Exception as e:
        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)
    


# Update booking status as completed or cancelled
@api_view(['PATCH'])
@permission_classes([
    IsAuthenticated,
    IsOwnerOrAdmin
])
def update_booking_status_by_owner(request, booking_id):

    try:

        booking = Booking.objects.filter(
            id=booking_id
        ).first()

        if not booking:

            return Response({
                "error": "Booking not found"
            }, status=404)
    
        status = request.GET.get("status")

        if status not in ["completed", "cancelled"]:
            return Response({
                "error": "Invalid status"
            }, status=400)
        
        if status == "cancelled":

            if booking.status == "cancelled":

                return Response({
                    "error": "Booking already cancelled"
                }, status=400)

            booking.status = "cancelled"
            booking.save()

            return Response({
                "message": "Booking marked as cancelled"
            })

        if status == "completed":
            if booking.status == "completed":
                return Response({
                    "error": "Booking already completed"
                }, status=400)

            booking.status = "completed"
            booking.save()

            return Response({
                "message": "Booking marked as completed"
            })

    except Exception as e:
        print(traceback.format_exc())

        return Response({
            "error": str(e)
        }, status=500)
    


# Customer cancel booking status
@api_view(['PATCH'])
@permission_classes([
    IsAuthenticated,
    IsCustomer
])
def cancel_booking_by_customer(request, booking_id):
    try:

        booking = Booking.objects.filter(
            id=booking_id,
            user_id=request.user.id
        ).first()


        if not booking:
            return Response({
                "error": "Booking not found"
            }, status=404)

        if booking.status == "completed":
            return Response({
                "error": "Completed booking cannot be cancelled"
            }, status=400)

        if booking.status == "cancelled":
            return Response({
                "error": "Booking already cancelled"
            }, status=400)

        # Prevent cancelling past bookings
        if booking.booking_date < date.today():
            return Response({
                "error": "Past bookings cannot be cancelled"
            }, status=400)

        booking.status = "cancelled"
        booking.save()

        return Response({
            "message": "Booking cancelled successfully"
        })

    except Exception as e:

        print(traceback.format_exc())
        return Response({
            "error": str(e)
        }, status=500)