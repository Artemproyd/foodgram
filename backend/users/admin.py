from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Subscription, User


class CustomUserAdmin(UserAdmin):
    search_fields = ('username', 'email', 'first_name', 'last_name')

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_active')


admin.site.register(Subscription)
admin.site.register(User, CustomUserAdmin)
