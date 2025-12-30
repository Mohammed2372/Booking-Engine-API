from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import SafeText

from .models import Booking, Review


# Register your models here.
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user_link",
        "room",
        "stay_dates",
        "total_price",
        "status_colored",
        "is_refunded",
    ]
    list_filter = ["status", "is_refunded", "created_at"]
    search_fields = ["user__username", "room__room_number", "stripe_payment_intent_id"]
    actions = ["mark_as_confirmed", "export_to_csv"]

    def user_link(self, obj) -> SafeText:
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username,
        )

    user_link.short_description = "Guest"

    def status_colored(self, obj) -> SafeText:
        colors = {
            "PENDING": "orange",
            "CONFIRMED": "green",
            "CANCELLED": "red",
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 5px; border-radius: 5px;">{}</span>',
            colors.get(obj.status, "black"),
            obj.status,
        )

    status_colored.short_description = "Status"

    def stay_dates(self, obj) -> SafeText:
        return f"{obj.stay_range.lower} -> {obj.stay_range.upper}"

    # Bulk action (Mark Confirmed)
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status="CONFIRMED")
        self.message_user(request, f"{updated} bookings marked as CONFIRMED.")

    mark_as_confirmed.short_description = "Mark selected bookings as Confirmed"

    # Bulk action (Export to CSV)
    def export_to_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="bookings.csv"'
        writer = csv.writer(response)

        writer.writerow(["ID", "User", "Room", "Price", "Status"])

        for booking in queryset:
            writer.writerow(
                [
                    booking.id,
                    booking.user.username,
                    booking.room,
                    booking.total_price,
                    booking.status,
                ]
            )

        return response

    export_to_csv.short_description = "Export selected to CSV"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["id", "booking__user", "booking", "rating", "comment", "created_at"]
    list_filter = ["created_at", "rating"]
