from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from .models import UserProfile, Wishlist


class UserProfileSerializer(ModelSerializer):
    username = serializers.CharField(source="user.username", required=False)
    email = serializers.CharField(source="user.email", read_only=True, required=False)
    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "phone_number",
            "address",
        ]

    def update(self, instance, validated_data):
        # update user model manually
        user_data = validated_data.pop("user", {})
        user = instance.user

        if "first_name" in user_data:
            user.first_name = user_data["first_name"]
        if "last_name" in user_data:
            user.last_name = user_data["last_name"]
        if "username" in user_data:
            user.username = user_data["username"]

        user.save()

        return super().update(instance, validated_data)


class WishlistSerializer(ModelSerializer):
    room_type_name = serializers.CharField(source="room_type.name", read_only=True)
    room_type_price = serializers.CharField(source="room_type.price", read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "room_type", "room_type_name", "room_type_price", "created_at"]
        read_only_fields = ["id", "created_at"]
