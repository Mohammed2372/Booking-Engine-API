from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


from .services import (
    calculate_total_price,
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
        available_types = find_available_room_types(
            parse_date(check_in_date), parse_date(check_out_date)
        )

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
            data = RoomTypeSerializer(filterset.qs).data
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

            # create booking
            try:
                booking = create_booking(
                    user=request.user,
                    room_type_id=data["room_type_id"],
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
                    comment=serializer.validate_data.get("comment", ""),
                )
                return Response(
                    {
                        "message": "Review submitted!",
                        "review": ReviewCreateSerializer(review),
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    {"error": "You have already reviewed this booking."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
