from django.db import models
from django.db.models import Model

from django.contrib.postgres.fields import ArrayField


# Create your models here.
class Property(Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    address = models.TextField()
    city = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.name


class RoomType(Model):
    class ViewType(models.TextChoices):
        CITY = "CITY", "City View"
        SEA = "SEA", "Sea View"
        GARDEN = "GARDEN", "Garden View"
        POOL = "POOL", "Pool View"

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="room_types"
    )
    name = models.CharField(max_length=255)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.PositiveIntegerField()
    view_type = models.CharField(
        max_length=20, choices=ViewType.choices, default=ViewType.CITY
    )
    is_smoking = models.BooleanField(default=False)

    amenities = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
    )

    def __str__(self) -> str:
        return f"{self.name} at {self.property.name}"


class Room(Model):
    number = models.CharField(max_length=10)
    room_type = models.ForeignKey(
        RoomType, on_delete=models.CASCADE, related_name="rooms"
    )

    def __str__(self):
        return f"room number: {self.number}, name: {self.room_type.name}"
