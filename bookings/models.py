from django.db import models
from django.db.models import Model, TextChoices
from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators, DateRangeField
from django.utils.translation import gettext_lazy as _

from inventory.models import Room


# Create your models here.
class Booking(Model):
    class Status(TextChoices):
        PENDING = "PENDING",_('Pending')
        CONFIRMED = "CONFIRMED",_('Confirmed')
        CANCELLED = "CANCELLED",_('Canceled')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')

    stay_range = DateRangeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        # constraints from the database itself
        constraints = [
            ExclusionConstraint(
                name='exclude_overlapping_bookings',
                expressions=[
                    ('stay_range', RangeOperators.OVERLAPS),
                    ('room', RangeOperators.EQUAL),
                ],
                condition=models.Q(status__in=['PENDING', 'CONFIRMED'])
            ),
        ]


    def __str__(self):
        return f'Booking {self.id} for {self.room}'
