from psycopg2.extras import DateRange
from datetime import date


from bookings.models import Booking
from .models import RoomType, Room


def find_available_room_types(check_in: date, check_out: date):
    # return a queryset of room types that has at least one physical free room in it for given dates
    search_range = DateRange(check_in, check_out)

    booked_room_ids = Booking.objects.filter(
        status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
        stay_range__overlap=search_range,
    ).values_list("room_id", flat=True)

    available_rooms = Room.objects.exclude(
        id__in=booked_room_ids,
    )

    available_room_types = RoomType.objects.filter(
        rooms__in=available_rooms,
    ).distinct()

    return available_room_types


def get_inventory_status(room_types_list, check_in, check_out):
    search_range = DateRange(check_in, check_out)

    for room_type in room_types_list:
        # count total physical rooms for every type
        total_rooms = room_type.rooms.count()

        # count rooms calculate busy rooms
        busy_rooms = (
            Room.objects.filter(
                room_type=room_type,
                bookings__stay_range__overlap=search_range,
                bookings__status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
            )
            .distinct()
            .count()
        )

        # calculate available rooms
        available_rooms = total_rooms - busy_rooms

        # room_type.total_inventory = total_rooms
        room_type.rooms_left = max(0, available_rooms)

    return room_types_list
