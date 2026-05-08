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

    reason = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "emergency_holidays"

    def save(self, *args, **kwargs):
        self.total_days = (
            self.end_date - self.start_date
        ).days + 1

        super().save(*args, **kwargs)