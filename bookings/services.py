from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError
from psycopg2.extras import DateRange
from datetime import date, timedelta

from inventory.models import PricingRule, Room, RoomType
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

        final_price = calculate_total_price(
            available_room.room_type,
            check_in,
            check_out,
        )
        
        booking = Booking.objects.create(
            user=user,
            room=available_room,
            stay_range=search_range,
            status=Booking.Status.PENDING,
            total_price=final_price,
        )

        return booking
    

def calculate_total_price(room_type, check_in: date, check_out: date):
    """
    Iterates through each day of the stay.
    Checks if any pricing rule applies to that specific day.
    Return the SUM of all daily prices.
    """
    
    total_price = 0.0
    current_date = check_in
    
    # get all rules for this room type
    rules = PricingRule.objects.filter(
        Q(room_type=room_type) | Q(room_type__isnull=True)
    )
    
    # loop through every single night
    while current_date < check_out:
        daily_price = float(room_type.base_price)
        multiplier = 1.0
        
        for rule in rules:
            # check if the date within the rule's range
            date_match = True
            if rule.start_date and rule.end_date:
                if not (rule.start_date <= current_date <= rule.end_date):
                    date_match = False
            
            # check if the day of week correct
            day_match = True
            if rule.days_of_week:
                if current_date.weekday() not in rule.days_of_week:
                    day_match = False
            
            # if both match, apply the math
            if date_match and day_match:
                multiplier *= float(rule.price_multiplier)
        
        # add this day's cost to total
        total_price += (daily_price * multiplier)
        
        # move to next day
        current_date += timedelta(days=1)
    return round(total_price, 2)


def get_inventory_status(room_types_list, check_in, check_out):
    search_range = DateRange(check_in, check_out)

    for room_type in room_types_list:
        # count total physical rooms for every type
        total_rooms = room_type.rooms.count()
        
        # count rooms calculate busy rooms
        busy_room_type = RoomType.objects.filter(
            room_type=room_type,
            bookings__stay_range__overlap=search_range,
            bookings__status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED]
        ).distinct().count()
        
        # calculate available rooms
        available_rooms = total_rooms - busy_room_type
        
        room_type.total_inventory = total_rooms
        room_type.rooms_left = max(0, available_rooms)
        
    return room_types_list
        