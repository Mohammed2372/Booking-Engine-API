from django.urls import path

from .views import (
    BookingCancelApIView,
    ReviewCreateAPIView,
    RoomSearchAPIView,
    BookingCreateAPIView,
)

urlpatterns = [
    path("search/", RoomSearchAPIView.as_view(), name="rooms-search"),
    path("book/", BookingCreateAPIView.as_view(), name="book-rooms-create"),
    path("review/", ReviewCreateAPIView.as_view(), name="create-review"),
    # TODO: make booking detail page
    path(
        "bookings/<int:pk>/cancel/",
        BookingCancelApIView.as_view(),
        name="cancel-booking",
    ),
]
