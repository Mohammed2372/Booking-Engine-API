from django.db import models
from django.db.models import Model

# Create your models here.
class Property(Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    address = models.TextField()
    city = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class RoomType(Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='room_types')
    name = models.CharField(max_length=255)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Room(Model):
    number = models.CharField(max_length=10)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rooms')

    def __str__(self):
        return f"room number: {self.number}, name: {self.room_type.name}"