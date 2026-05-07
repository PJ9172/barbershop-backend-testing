from django.db import models

# Create your models here.

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)

    duration = models.IntegerField(help_text="Duration in minutes")  # 🔥 important

    is_active = models.BooleanField(default=True)  # 🔥 soft delete

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    


class BarberShopSettings(models.Model):

    opening_time = models.TimeField()
    closing_time = models.TimeField()

    lunch_start_time = models.TimeField(null=True, blank=True)
    lunch_end_time = models.TimeField(null=True, blank=True)

    slot_duration = models.IntegerField(default=60)

    week_holiday = models.IntegerField(
        null=True,
        blank=True,
        help_text="0=Monday ... 6=Sunday"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "barber_shop_settings"


class EmergencyHoliday(models.Model):
    holiday_date = models.DateField(unique=True)
    reason = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "emergency_holidays"