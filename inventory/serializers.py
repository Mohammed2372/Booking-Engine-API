from rest_framework import serializers
from rest_framework.serializers import ModelSerializer


from .models import RoomType, RoomImage


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
