from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


from .services import find_available_room_types, create_booking
from .serializers import (
    BookingCreateSerializer,
    BookingDetailSerializer,
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

        # find room types
        available_types = find_available_room_types(
            parse_date(check_in), parse_date(check_out)
        )

        filterset = RoomTypeFilter(request.GET, queryset=available_types)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = RoomTypeSerializer(filterset.qs, many=True)
        return Response(serializer.data)


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
