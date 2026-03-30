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
    

