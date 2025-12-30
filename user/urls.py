from django.urls import path

from .views import UserProfileView, WishlistView

urlpatterns = [
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("wishlist/", WishlistView.as_view(), name="user-wishlist"),
]
