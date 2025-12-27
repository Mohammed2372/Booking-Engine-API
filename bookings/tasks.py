from celery import shared_task
from django.utils import timezone
from datetime import timedelta


from .models import Booking


@shared_task
def cancel_expired_bookings():
    """
    Finds bookings that are 'PENDING' and older than 15 minutes.
    Marks them as 'CANCELLED' to free up inventory.
    """
    timeout_threshold = timezone.now() - timedelta(minutes=15)

    expired_bookings = Booking.objects.filter(
        status=Booking.Status.PENDING,
        created_at__lt=timeout_threshold,
    )

    # get count of expired bookings
    count = expired_bookings.count()

    if count > 0:
        # use bulk update as it is faster than looping
        expired_bookings.update(status=Booking.Status.CANCELLED)
        return f"Cancelled {count} expired bookings."

    return "No expired bookings found."
