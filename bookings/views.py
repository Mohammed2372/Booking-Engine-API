from django.db.models.manager import BaseManager
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView, RetrieveAPIView
from drf_spectacular.utils import extend_schema

import stripe

from core import settings
from .services import (
    cancel_booking,
    create_payment_intent,
    create_booking,
)
from .models import Booking, Review
from .serializers import (
    BookingCreateSerializer,
    BookingDetailSerializer,
    ReviewCreateSerializer,
)
from inventory.models import RoomType


# Create your views here.
class BookingCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingCreateSerializer

    @extend_schema(
        request=BookingCreateSerializer,
        responses={201: BookingDetailSerializer},
        description="Book a specific room type. Requires authentication.",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            # convert slug to ID
            try:
                room_type = RoomType.objects.get(slug=data["room_type_slug"])
            except RoomType.DoesNotExist:
                return Response(
                    {"error": "Invalid room type name."},
                    status=400,
                )

            # create booking
            try:
                booking = create_booking(
                    user=request.user,
                    room_type_id=room_type.id,
                    check_in=data["check_in"],
                    check_out=data["check_out"],
                )

                return Response(
                    BookingDetailSerializer(booking).data,
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingCheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: "Stripe Client Secret"},
        description="Generates a Stripe Payment Intent for this booking.",
    )
    def post(self, request, booking_id):
        # get booking
        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found."}, status=400)

        # check if already paid
        if booking.status == Booking.Status.CONFIRMED:
            return Response({"error": "Booking is already paid"}, status=200)

        # create stripe intent
        try:
            client_secret = create_payment_intent(booking)
            return Response(
                {
                    "client_secret": client_secret,
                    "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class BookingListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingDetailSerializer

    def get_queryset(self) -> BaseManager[Booking]:
        return Booking.objects.filter(user=self.request.user).order_by("-id")


class BookingRetrieveAPIView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingDetailSerializer
    lookup_field = "id"
    lookup_url_kwarg = "booking_id"

    def get_queryset(self) -> BaseManager[Booking]:
        return Booking.objects.filter(user=self.request.user)


class BookingCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: "Booking Cancelled"},
        description="Cancel a booking. Applies penalty if within 48 hours check in.",
    )
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)
        except Booking.DoesNotExist:
            return Response(
                {"error": "Booking not found."}, status=status.HTTP_400_BAD_REQUEST
            )

        # call service
        try:
            cancelled_booking = cancel_booking(booking)

            return Response(
                {
                    "status": "cancelled",
                    "refund_amount": cancelled_booking.refund_amount,
                    "penalty_applied": cancelled_booking.penalty_applied,
                    "message": f"Booking cancelled successfully for booking number ({booking_id}).",
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=400)


class ReviewCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ReviewCreateSerializer,
        responses={201: "Review Created"},
        description="Submit a review for a specific booking ID.",
    )
    def post(self, request):
        serializer = ReviewCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            booking = Booking.objects.get(id=serializer.validated_data["booking_id"])

            try:
                review = Review.objects.create(
                    booking=booking,
                    rating=serializer.validated_data["rating"],
                    comment=serializer.validated_data.get("comment", ""),
                )
                return Response(
                    {
                        "message": "Review submitted!",
                        "review": ReviewCreateSerializer(review).data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
