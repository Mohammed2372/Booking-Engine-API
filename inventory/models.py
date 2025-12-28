from django.db import models
from django.db.models import Model, TextChoices, Avg
from autoslug import AutoSlugField
from django.contrib.postgres.fields import ArrayField

import builtins


# Create your models here.
class Property(Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    address = models.TextField()
    city = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.name


class RoomType(Model):
    class ViewType(TextChoices):
        CITY = "CITY", "City View"
        SEA = "SEA", "Sea View"
        GARDEN = "GARDEN", "Garden View"
        POOL = "POOL", "Pool View"

    class RoomKind(TextChoices):
        SINGLE = "SINGLE", "Single Room"
        DOUBLE = "DOUBLE", "Double Room"
        TWIN = "TWIN", "Twin Room"
        STUDIO = "STUDIO", "Studio"
        DELUXE = "DELUXE", "Deluxe Suite"
        FAMILY = "FAMILY", "Family Suite"
        PRESIDENTIAL = "PRESIDENTIAL", "Presidential Suite"

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="room_types"
    )
    name = models.CharField(
        max_length=50, choices=RoomKind.choices, default=RoomKind.SINGLE
    )
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.PositiveIntegerField(help_text="Max people allowed")
    view_type = models.CharField(
        max_length=20, choices=ViewType.choices, default=ViewType.CITY
    )
    is_smoking = models.BooleanField(default=False)

    amenities = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
    )
    slug = AutoSlugField(populate_from="name", unique=True, always_update=True)

    def __str__(self) -> str:
        return f"{self.name} at {self.property.name}"

    @builtins.property
    def average_rating(self):
        # Joins Room -> Booking -> Review -> Calculates Average
        # Returns None if no reviews exist

        avg = self.rooms.aggregate(avg_score=Avg("bookings__review__rating"))[
            "avg_score"
        ]

        return round(avg, 1) if avg else 0.0

    @builtins.property
    def review_count(self):
        return self.rooms.filter(bookings__review__isnull=False).count()


class Room(Model):
    number = models.CharField(max_length=10)
    room_type = models.ForeignKey(
        RoomType, on_delete=models.CASCADE, related_name="rooms"
    )

    def __str__(self):
        return f"room number: {self.number}, name: {self.room_type.name}"


class RoomImage(Model):
    room_type = models.ForeignKey(
        RoomType, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="room_images/")
    is_cover = models.BooleanField(
        default=False, help_text="Is this the main image shown in search?"
    )
    caption = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Image for {self.room_type.name}"


class PricingRule(Model):
    name = models.CharField(max_length=100)
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="priding_rules",
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    days_of_week = ArrayField(
        models.PositiveIntegerField(),
        null=True,
        blank=True,
        help_text="0=Monday, 6=Sunday",
    )
    price_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.00,
        help_text="Standard, 1.2 = +20%, 0.8 = -20%",
    )

    def __str__(self):
        return f"{self.name} (x{self.price_multiplier})"
