from django.urls import path

from .views import UserProfileView, WishlistView, ReviewCreateAPIView

urlpatterns = [
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("wishlist/", WishlistView.as_view(), name="user-wishlist"),
    path("review/", ReviewCreateAPIView.as_view(), name="create-review"),
]
