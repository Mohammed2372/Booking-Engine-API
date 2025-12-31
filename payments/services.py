from django.conf import settings

import stripe


def create_payment_intent(booking):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if booking.total_price <= 0:
        raise ValueError("Booking price must be greater than zero.")

    try:
        amount_in_cents = int(booking.total_price * 100)

        # create intent
        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency="usd",
            metadata={
                "booking_id": booking.id,
                "user_email": booking.user.email,
            },
        )

        # save intent ID
        booking.stripe_payment_intent_id = intent.id
        booking.save()

        return intent["client_secret"]
    except Exception as e:
        raise Exception(f"Stript error {str(e)}")
