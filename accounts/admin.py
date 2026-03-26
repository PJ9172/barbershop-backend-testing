from django.contrib import admin
from .models import User, Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'mobile_no', 'first_name', 'last_name', 'role', 'is_active')
    search_fields = ('mobile_no', 'first_name', 'last_name')
    list_filter = ('role', 'is_active')