from django.contrib import admin

from .models import UserProfile, Wishlist

# Register your models here.
admin.register(UserProfile)
admin.register(Wishlist)