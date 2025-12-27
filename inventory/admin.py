from django.contrib import admin

from .models import Property, RoomType, Room

# Register your models here.
admin.site.register(Property)
admin.site.register(RoomType)
admin.site.register(Room)
