from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


from .models import RoomType
from .serializers import RoomTypeSerializer
from .services import (
    calculate_total_price,
    find_available_room_types,
    get_inventory_status,
)
from .filters import RoomTypeFilter


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
