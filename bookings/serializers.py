from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, Serializer

from .models import Booking, Review
from inventory.models import RoomType, RoomImage


class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ["image", "is_cover", "caption"]


class RoomTypeSerializer(ModelSerializer):
    hotel_name = serializers.CharField(source="property.name", read_only=True)
    city = serializers.CharField(source="property.city", read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.FloatField(read_only=True)
    # total_inventory = serializers.IntegerField(read_only=True)
    rooms_left = serializers.IntegerField(read_only=True)

    class Meta:
        model = RoomType
        fields = [
            "id",
            "slug",
            "hotel_name",
            "city",
            "name",
            "base_price",
            "capacity",
            "view_type",
            "amenities",
            "is_smoking",
            "images",
            "average_rating",
            "review_count",
            "rooms_left",
        ]


class BookingCreateSerializer(Serializer):
    """Input validation for creating booking"""

    # room_type_id = serializers.IntegerField()
    room_type_slug = serializers.SlugField()
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
            "cancelled_at",
            "refund_amount",
            "penalty_applied",
        ]

    def get_check_in(self, obj):
        return obj.stay_range.lower if obj.stay_range else None

    def get_check_out(self, obj):
        return obj.stay_range.upper if obj.stay_range else None

    def get_thumbnail(self, obj):
        return obj.room.room_type.images[0] if obj.room.room_type.images else None


class ReviewCreateSerializer(ModelSerializer):
    booking_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Review
        fields = ["booking_id", "rating", "comment", "created_at"]
        read_only_fields = ["created_at"]

    def validate_booking_id(self, value):
        user = self.context["request"].user

        # check if the booking exists and belong to this user
        try:
            booking = Booking.objects.get(id=value, user=user)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Invalid booking ID.")

        # check if booking is complete only, can't review without booking
        if booking.status != Booking.Status.CONFIRMED:
            raise serializers.ValidationError("You can only review completed stays.")
        return value
