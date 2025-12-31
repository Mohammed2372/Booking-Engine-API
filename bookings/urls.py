from django.urls import path

from .views import (
    BookingCancelAPIView,
    BookingCheckoutAPIView,
    BookingListAPIView,
    BookingRetrieveAPIView,
    BookingCreateAPIView,
)

urlpatterns = [
    path("book/", BookingCreateAPIView.as_view(), name="book-rooms-create"),
    path("bookings/", BookingListAPIView.as_view(), name="my-bookings"),
    path(
        "bookings/<int:booking_id>/",
        BookingRetrieveAPIView.as_view(),
        name="booking-detail",
    ),
    path(
        "bookings/<int:booking_id>/checkout/",
        BookingCheckoutAPIView.as_view(),
        name="booking-checkout",
    ),
    path(
        "bookings/<int:booking_id>/cancel/",
        BookingCancelAPIView.as_view(),
        name="cancel-booking",
    ),
]
