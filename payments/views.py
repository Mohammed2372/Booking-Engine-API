from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework.views import APIView

import stripe

from core import settings
from bookings.models import Booking


# Create your views here.
@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookAPIView(APIView):
    permission_classes = []

    def post(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = settings.STRIPE_WEBHOOK_KEY

        event = None

        try:
            # verify signature
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=endpoint_secret,
            )
        except ValueError:
            return HttpResponse(status=400)  # invalid payload
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)  # invalid signature

        # handle event
        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            stripe_id = payment_intent["id"]

            # find and update booking
            try:
                booking = Booking.objects.get(
                    stripe_payment_intent_id=stripe_id,
                    status=Booking.Status.PENDING,  # to ensure that it is really waiting to be paid
                )
                booking.status = Booking.Status.CONFIRMED
                booking.is_refunded = False  # reset just in case
                booking.save()
                print(
                    f"✅ Booking ({booking.id}) for room (number: {booking.room.number}, name: {booking.room.room_type.slug}) for user {booking.user}."
                )
            except Booking.DoesNotExist:
                print(f"⚠️ Payment succeeded for unknown booking: {stripe_id}")

        return HttpResponse(status=200)
