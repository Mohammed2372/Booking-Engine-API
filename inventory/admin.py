from django.contrib import admin

from .models import PricingRule, Property, RoomImage, RoomType, Room


# Register your models here.
class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    inlines = [RoomImageInline]
    list_display = [
        "name",
        "property",
        "base_price",
        "slug",
        "capacity",
        "view_type",
        "is_smoking",
    ]


admin.site.register(Property)
# admin.site.register(RoomType)
admin.site.register(Room)
admin.site.register(PricingRule)
