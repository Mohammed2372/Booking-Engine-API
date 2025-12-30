from django.urls import path

from .views import RoomSearchAPIView


urlpatterns = [
    path("search/", RoomSearchAPIView.as_view(), name="rooms-search"),
]
