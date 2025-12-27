from django.urls import path

from .views import RoomSearchAPIView, BookingCreateAPIView

urlpatterns = [
    path('search/', RoomSearchAPIView.as_view(), name='rooms-search'),
    path('book/', BookingCreateAPIView.as_view(), name='book-rooms-create'),
]