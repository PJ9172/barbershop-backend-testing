from django.db import models
from accounts.models import User
# Create your models here.


# Category and Service models
class Category(models.Model):

    name = models.CharField(max_length=100, unique=True, default="General")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categories"
    def __str__(self):
        return self.name
    

class Service(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,   # 🔥 important
        related_name="services"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(
        null=True,
        blank=True
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    duration = models.IntegerField(
        help_text="Duration in minutes"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "services"
    def __str__(self):
        return self.name
    


# Settings and Holiday models
class BarberShopSettings(models.Model):

    opening_time = models.TimeField()
    closing_time = models.TimeField()

    lunch_start_time = models.TimeField(null=True, blank=True)
    lunch_end_time = models.TimeField(null=True, blank=True)

    slot_duration = models.IntegerField(default=30)
    slot_capacity = models.IntegerField(default=1)

    week_holiday = models.CharField(max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "barber_shop_settings"


class EmergencyHoliday(models.Model):

    enabled = models.BooleanField(default=False)

    start_date = models.DateField()
    end_date = models.DateField()

    total_days = models.IntegerField(editable=False)

    reason = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "emergency_holidays"

    def save(self, *args, **kwargs):
        self.total_days = (
            self.end_date - self.start_date
        ).days + 1

        super().save(*args, **kwargs)


# Booking model
class Booking(models.Model):

    BOOKING_TYPE_CHOICES = [
        ("online", "Online"),
        ("offline", "Offline")
    ]

    STATUS_CHOICES = [
        ("booked", "Booked"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled")
    ]

    PAYMENT_METHOD_CHOICES = [
    ("cash", "Cash"),
    ("upi", "UPI"),
    ("card", "Card"),
]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    customer_name = models.CharField(
        max_length=100
    )

    customer_mobile_no = models.CharField(
        max_length=15
    )

    customer_email = models.EmailField(
        null=True,
        blank=True
    )

    services = models.ManyToManyField(Service)

    booking_date = models.DateField()

    start_time = models.TimeField(default="00:00")
    end_time = models.TimeField(default="00:00")

    total_duration = models.IntegerField(default=0)

    total_amount = models.DecimalField(
        max_digits=10,
        default=0.00,
        decimal_places=2
    )

    booking_type = models.CharField(
        max_length=20,
        choices=BOOKING_TYPE_CHOICES,
        default="online"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="booked"
    )

    payment_method = models.CharField(
    max_length=20,
    choices=PAYMENT_METHOD_CHOICES,
    default="cash"
)
    
    created_at = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_bookings"
    )

    class Meta:
        db_table = "bookings"



# Coupon model
class Coupon(models.Model):

    DISCOUNT_TYPE_CHOICES = [
        ("percentage", "Percentage"),
        ("flat", "Flat")
    ]

    code = models.CharField(
        max_length=50,
        unique=True
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES
    )

    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    min_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    valid_till = models.DateField()
    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.code