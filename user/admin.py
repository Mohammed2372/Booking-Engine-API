from typing import Literal
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import SafeText

from .models import Review, UserProfile, Wishlist


# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone_number", "avatar_thumbnail"]
    search_fields = ["user__username", "phone_number"]

    def avatar_thumbnail(self, obj) -> SafeText | Literal["No Image"]:
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 50%;" />',
                obj.avatar.url,
            )
        return "No Image"

    avatar_thumbnail.short_description = "Avatar"


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["user", "room_type", "created_at"]
    list_filter = ["created_at"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["id", "booking__user", "booking", "rating", "comment", "created_at"]
    list_filter = ["created_at", "rating"]
