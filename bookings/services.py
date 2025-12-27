from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError
from psycopg2.extras import DateRange
from datetime import date

from inventory.models import Room, RoomType
from bookings.models import Booking

# TODO: Availability search -> find a room type ('deluxe') that has at least one physical room free
def find_available_room_types(check_in: date, check_out: date):
    # return a queryset of room types that has at least one physical free room in it for given dates
    search_range = DateRange(check_in, check_out)

    booked_room_ids = Booking.objects.filter(
        status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
        stay_range__overlap=search_range,
    ).values_list('room_id', flat=True)

    available_rooms = Room.objects.exclude(id__in=booked_room_ids,)

    available_room_types = RoomType.objects.filter(
        rooms__in=available_rooms,
    ).distinct()

    return available_room_types

# TODO: Allocation -> pick a specific room number (room 101) for the user
def create_booking(user, room_type_id, check_in: date, check_out: date):
    search_range = DateRange(check_in, check_out)

    with transaction.atomic():
        booked_ids = Booking.objects.filter(
            stay_range__overlap=search_range,
            status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
        ).values_list('room_id', flat=True)

        # try to find available room with given type
        available_room = Room.objects.select_for_update(skip_locked=True).filter(
            room_type_id=room_type_id,
        ).exclude(
            id__in=booked_ids,
        ).first()

        if not available_room:
            raise ValidationError('No rooms available for these dates')

        booking = Booking.objects.create(
            user=user,
            room=available_room,
            stay_range=search_range,
            status=Booking.Status.PENDING,
        )

        return booking