from django.contrib import admin

from .models import Booking, Review


# Register your models here.
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "room", "status", "total_price"]
    list_filter = ["status"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["id", "booking__user", "booking", "rating", "comment", "created_at"]
    list_filter = ["created_at", "rating"]
