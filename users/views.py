from django.shortcuts import render

from rest_framework.decorators import (
    api_view,
    permission_classes
)

from rest_framework.permissions import (
    IsAuthenticated
)

from rest_framework.response import Response

from barber.models import Booking

import traceback


# Get all bookings for a user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_bookings(request):

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