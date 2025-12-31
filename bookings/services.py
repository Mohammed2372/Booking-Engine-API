from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils import timezone
from psycopg2.extras import DateRange
from datetime import date, timedelta

from inventory.models import PricingRule, Room
from bookings.models import Booking


def create_booking(user, room_type_id, check_in: date, check_out: date):
    search_range = DateRange(check_in, check_out)

    with transaction.atomic():
        booked_ids = Booking.objects.filter(
            stay_range__overlap=search_range,
            status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
        ).values_list("room_id", flat=True)

        # try to find available room with given type
        available_room = (
            Room.objects.select_for_update(skip_locked=True)
            .filter(
                room_type_id=room_type_id,
            )
            .exclude(
                id__in=booked_ids,
            )
            .first()
        )

        if not available_room:
            raise ValidationError("No rooms available for these dates")

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
        total_price += daily_price * multiplier

        # move to next day
        current_date += timedelta(days=1)
    return round(total_price, 2)


def cancel_booking(booking):
    # check on booking
    if booking.status == Booking.Status.CANCELLED:
        raise ValidationError(f"Booking number {booking.id} is already cancelled")

    # extract check in and check out dates
    check_in = booking.stay_range.lower
    check_out = booking.stay_range.upper

    # calculate time difference
    now = timezone.now()
    check_in_datetime = timezone.datetime.combine(
        check_in, timezone.datetime.min.time()
    )
    check_in_datetime = timezone.make_aware(check_in_datetime)
    time_until_check_in = check_in_datetime - now

    # define policy
    hours_left = time_until_check_in.total_seconds() / 3600
    total_paid = booking.total_price
    refund_amount = total_paid
    has_penalty = False

    if hours_left < 48:
        # check on penalty
        nights = (check_out - check_in).days
        one_night_rate = total_paid / nights if nights > 0 else total_paid

        refund_amount = max(Decimal("0.00"), total_paid - one_night_rate)
        has_penalty = True

    # update database
    booking.status = Booking.Status.CANCELLED
    booking.cancelled_at = now
    booking.refund_amount = refund_amount
    booking.penalty_applied = has_penalty
    booking.is_refunded = True
    booking.save()

    return booking
