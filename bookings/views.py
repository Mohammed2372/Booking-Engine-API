from django.db.models.manager import BaseManager
from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListAPIView, RetrieveAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .services import (
    calculate_total_price,
    cancel_booking,
    find_available_room_types,
    create_booking,
    get_inventory_status,
)
from .models import Booking, Review
from .serializers import (
    BookingCreateSerializer,
    BookingDetailSerializer,
    ReviewCreateSerializer,
    RoomTypeSerializer,
)
from .filters import RoomTypeFilter
from inventory.models import RoomType


# Create your views here.
class RoomSearchAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="check_in",
                description="Start Date",
                required=True,
                type=OpenApiTypes.DATE,
            ),
            OpenApiParameter(
                name="check_out",
                description="End Date",
                required=True,
                type=OpenApiTypes.DATE,
            ),
            OpenApiParameter(
                name="city", required=False, type=str, description="Filter by City"
            ),
            OpenApiParameter(
                name="capacity", required=False, type=int, description="Min people"
            ),
            OpenApiParameter(
                name="view_type",
                required=False,
                type=str,
                enum=[c[0] for c in RoomType.ViewType.choices],
                description="Filter by View Type",
            ),
            OpenApiParameter(
                name="name",
                description="Room King (e.g. DELUXE, SINGLE)",
                required=True,
                type=str,
                enum=[c[0] for c in RoomType.RoomKind.choices],
            ),
        ],
        responses=RoomTypeSerializer(many=True),
        description="Find all room types with at least one available room for given date",
    )
    def get(self, request):
        check_in = request.query_params.get("check_in")
        check_out = request.query_params.get("check_out")

        if not check_in or not check_out:
            return Response(
                {"error": "Please provide 'check_in' and 'check_out' dates"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        check_in_date = parse_date(check_in)
        check_out_date = parse_date(check_out)

        # find room types
        available_types = find_available_room_types(check_in_date, check_out_date)

        # filter
        filterset = RoomTypeFilter(request.GET, queryset=available_types)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        # get counts of filtered room types
        room_types = get_inventory_status(filterset.qs, check_in_date, check_out_date)

        # calculate total price for each result
        results = []
        for room_type in room_types:
            total_price = calculate_total_price(
                room_type, check_in_date, check_out_date
            )

            # convert model to dictionary
            data = RoomTypeSerializer(room_type).data
            # inject new field in the model
            data["total_price_for_stay"] = total_price
            results.append(data)

        # sort most available rooms at top
        results.sort(key=lambda x: x["rooms_left"], reverse=True)

        return Response(results)


class BookingCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingCreateSerializer

    @extend_schema(
        request=BookingCreateSerializer,
        responses={201: BookingDetailSerializer},
        description="Book a specific room type. Requires authentication.",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            # convert slug to ID
            try:
                room_type = RoomType.objects.get(slug=data["room_type_slug"])
            except RoomType.DoesNotExist:
                return Response(
                    {"error": "Invalid room type name."},
                    status=400,
                )

            # create booking
            try:
                booking = create_booking(
                    user=request.user,
                    room_type_id=room_type.id,
                    check_in=data["check_in"],
                    check_out=data["check_out"],
                )

                return Response(
                    BookingDetailSerializer(booking).data,
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingDetailSerializer

    def get_queryset(self) -> BaseManager[Booking]:
        return Booking.objects.filter(user=self.request.user).order_by("-id")


class BookingRetrieveAPIView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingDetailSerializer
    lookup_field = "id"

    def get_queryset(self) -> BaseManager[Booking]:
        return Booking.objects.filter(user=self.request.user)


class BookingCancelApIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: "Booking Cancelled"},
        description="Cancel a booking. Applies penalty if within 48 hours check in.",
    )
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)
        except Booking.DoesNotExist:
            return Response(
                {"error": "Booking not found."}, status=status.HTTP_400_BAD_REQUEST
            )

        # call service
        try:
            cancelled_booking = cancel_booking(booking)

            return Response(
                {
                    "status": "cancelled",
                    "refund_amount": cancelled_booking.refund_amount,
                    "penalty_applied": cancelled_booking.penalty_applied,
                    "message": "Booking cancelled successfully.",
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=400)


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
