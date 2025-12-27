from django.urls import path

from .views import ReviewCreateAPIView, RoomSearchAPIView, BookingCreateAPIView

urlpatterns = [
    path("search/", RoomSearchAPIView.as_view(), name="rooms-search"),
    path("book/", BookingCreateAPIView.as_view(), name="book-rooms-create"),
    path("review/", ReviewCreateAPIView.as_view(), name="create-review"),
]
