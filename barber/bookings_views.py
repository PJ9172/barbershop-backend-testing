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
    


# Save a new booking
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking(request):

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

        if not service_ids:
            return Response({
                "error": "No services selected"
            }, status=400)

        services = Service.objects.filter(
            id__in=service_ids,
            is_active=True
        )

        if not services.exists():
            return Response({
                "error": "Invalid services"
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

        settings_obj = BarberShopSettings.objects.first()

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

        with transaction.atomic():

            booking = Booking.objects.create(
                user=request.user,

                booking_date=booking_date,

                start_time=start_time,
                end_time=end_time,

                total_duration=total_duration,
                total_amount=total_amount
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
                    f"{booking.user.first_name} "
                    f"{booking.user.last_name}",

                "mobile_no":
                    booking.user.mobile_no,

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

        if status_filter:
            bookings = bookings.filter(
                status=status_filter
            )

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