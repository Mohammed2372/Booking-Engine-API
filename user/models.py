from django.db import models
from django.db.models import Model
from django.db.models.signals import post_save
from django.conf import settings
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

from inventory.models import RoomType
from bookings.models import Booking


# Create your models here.
class UserProfile(Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.user.username} Profile."


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class Wishlist(Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "room_type")  # to prevent duplicate likes

    def __str__(self) -> str:
        return f"{self.user.username} liked {self.room_type.name}"


class Review(Model):
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="review"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Start rating 1-5",
    )
    comment = models.TextField(blank=True)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.rating} stars  by {self.booking.user.username} for room {self.booking.room.number} in {self.booking.room.room_type.property.name}"
