from django.db import models
from accounts.models import User
# Create your models here.

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


from datetime import timedelta

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


class Booking(models.Model):

    STATUS_CHOICES = [
        ("booked", "Booked"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled")
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
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

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="booked"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bookings"