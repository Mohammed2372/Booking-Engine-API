from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, Serializer

from .models import Booking
from inventory.models import RoomType


class RoomTypeSerializer(ModelSerializer):
    hotel_name = serializers.CharField(source="property.name", read_only=True)
    city = serializers.CharField(source="property.city", read_only=True)

    class Meta:
        model = RoomType
        fields = ["id", "name", "base_price", "capacity"]


class BookingCreateSerializer(Serializer):
    """Input validation for creating booking"""

    room_type_id = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()

    def validate(self, attrs):
        if attrs["check_in"] >= attrs["check_out"]:
            raise serializers.ValidationError("Check-out must be after check-in")
        return attrs


class BookingDetailSerializer(ModelSerializer):
    room_name = serializers.CharField(source="room.room_type.name", read_only=True)
    room_number = serializers.CharField(source="room.number", read_only=True)

    # custom fields to extract dates from the Range object
    check_in = serializers.SerializerMethodField()
    check_out = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "status",
            "total_price",
            "check_in",
            "check_out",
            "room_name",
            "room_number",
        ]

    def get_check_in(self, obj):
        return obj.stay_range.lower if obj.stay_range else None

    def get_check_out(self, obj):
        return obj.stay_range.upper if obj.stay_range else None
