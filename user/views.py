from django.db.models.manager import BaseManager
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from inventory.models import RoomType
from bookings.models import Booking
from .models import UserProfile, Wishlist, Review
from .serializers import (
    UserProfileSerializer,
    WishlistSerializer,
    ReviewCreateSerializer,
)


# Create your views here.
class UserProfileView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self) -> UserProfile:
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class WishlistView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistSerializer

    def get_queryset(self) -> BaseManager[Wishlist]:
        return Wishlist.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Custom Logic: Toggle Behavior
        room_type_id = request.data.get("room_type")
        room_type = RoomType.objects.get(id=room_type_id)

        wishlist_item, created = Wishlist.objects.get_or_create(
            room_type=room_type,
            user=request.user,
        )

        if not created:
            # if is already exists then delete it
            wishlist_item.delete()
            return Response(
                {"message": "Removed from wishlist."}, status=status.HTTP_200_OK
            )

        return Response(
            self.get_serializer(wishlist_item).data, status=status.HTTP_201_CREATED
        )


class ReviewCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ReviewCreateSerializer,
        responses={201: "Review Created"},
        description="Submit a review for a specific booking ID.",
    )
    def post(self, request):
        serializer = ReviewCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            booking = Booking.objects.get(id=serializer.validated_data["booking_id"])

            try:
                review = Review.objects.create(
                    booking=booking,
                    rating=serializer.validated_data["rating"],
                    comment=serializer.validated_data.get("comment", ""),
                )
                return Response(
                    {
                        "message": "Review submitted!",
                        "review": ReviewCreateSerializer(review).data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
