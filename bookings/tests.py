from rest_framework.test import APITestCase, override_settings
from rest_framework import status
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from unittest.mock import patch, MagicMock
from psycopg2.extras import DateRange

# Import your models
from inventory.models import Room, RoomType, PricingRule, Property
from bookings.models import Booking
from bookings.tasks import cancel_expired_bookings


@override_settings(
    REST_FRAMEWORK={"DEFAULT_THROTTLE_CLASSES": [], "DEFAULT_THROTTLE_RATES": {}}
)
class MasterSystemTest(APITestCase):
    def setUp(self):
        # 1. SETUP USERS
        self.user = User.objects.create_user(
            username="tester", email="test@test.com", password="password123"
        )
        self.admin = User.objects.create_superuser(
            username="admin", password="password123"
        )

        # 2. SETUP AUTH (The Fix: Force Auth instead of Login Request)
        # This bypasses the 429 Throttling error completely
        self.client.force_authenticate(user=self.user)

        # 3. SETUP PROPERTY
        self.property = Property.objects.create(
            name="Test Hotel", description="Best hotel ever"
        )

        # 4. SETUP INVENTORY
        self.room_type = RoomType.objects.create(
            name="Deluxe Suite",
            slug="deluxe-suite",
            base_price=Decimal("100.00"),
            capacity=2,
            property=self.property,
        )
        self.room = Room.objects.create(number="101", room_type=self.room_type)

        # 5. SETUP PRICING RULE
        self.weekend_rule = PricingRule.objects.create(
            name="Weekend Hike",
            price_multiplier=Decimal("1.20"),
            days_of_week=[4, 5],  # Fri, Sat
        )

        # URLs
        self.url_create = "/api/book/"
        self.url_list = "/api/bookings/"
        self.url_webhook = "/api/webhook/"

    # ---------------------------------------------------------
    # TEST 1: PRICING ENGINE & CREATION
    # ---------------------------------------------------------
    def test_dynamic_pricing_calculation(self):
        check_in = "2025-01-03"
        check_out = "2025-01-05"

        data = {
            "room_type_slug": self.room_type.slug,
            "check_in": check_in,
            "check_out": check_out,
            "guests": 2,
        }

        response = self.client.post(self.url_create, data, format="json")

        if response.status_code != 201:
            print(f"\n⚠️ Create Failed: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        price = Decimal(response.data["total_price"])
        # 2 nights * 100 * 1.2 (weekend) = 240
        expected_price = Decimal("240.00")
        self.assertEqual(price, expected_price)

    # ---------------------------------------------------------
    # TEST 2: ZOMBIE KILLER (EXPIRATION)
    # ---------------------------------------------------------
    def test_zombie_expiration_logic(self):
        stay_range = DateRange(date(2025, 2, 1), date(2025, 2, 5))

        booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            stay_range=stay_range,
            total_price=Decimal("400.00"),
            status=Booking.Status.PENDING,
        )

        # Time Travel
        booking.created_at = timezone.now() - timedelta(minutes=20)
        booking.save()

        # Run Task
        cancel_expired_bookings()

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.EXPIRED)

    # ---------------------------------------------------------
    # TEST 3: PAYMENT "GOD MODE"
    # ---------------------------------------------------------
    @patch("stripe.PaymentIntent.confirm")
    def test_checkout_god_mode(self, mock_stripe_confirm):
        stay_range = DateRange(date(2025, 3, 1), date(2025, 3, 5))

        booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            stay_range=stay_range,
            total_price=Decimal("400.00"),
            status=Booking.Status.PENDING,
            stripe_payment_intent_id="pi_test_123",
        )

        mock_stripe_confirm.return_value = MagicMock(status="succeeded")

        url = f"/api/bookings/{booking.id}/checkout/"
        data = {"auto_confirm": True}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    # ---------------------------------------------------------
    # TEST 4: STRIPE WEBHOOK
    # ---------------------------------------------------------
    @patch("stripe.Webhook.construct_event")
    def test_stripe_webhook_success(self, mock_construct_event):
        intent_id = "pi_real_deal_123"
        stay_range = DateRange(date(2025, 4, 1), date(2025, 4, 5))

        booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            stay_range=stay_range,
            total_price=Decimal("400.00"),
            status=Booking.Status.PENDING,
            stripe_payment_intent_id=intent_id,
        )

        mock_event = {
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": intent_id}},
        }
        mock_construct_event.return_value = mock_event

        self.client.credentials()
        response = self.client.post(self.url_webhook, {}, format="json")
        self.assertEqual(response.status_code, 200)

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    # ---------------------------------------------------------
    # TEST 5: CANCELLATION & REFUNDS
    # ---------------------------------------------------------
    def test_cancellation_penalty_logic(self):
        tmrw = timezone.now().date() + timedelta(days=1)
        stay_range = DateRange(tmrw, tmrw + timedelta(days=5))

        booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            stay_range=stay_range,
            total_price=Decimal("500.00"),
            status=Booking.Status.CONFIRMED,
        )

        url = f"/api/bookings/{booking.id}/cancel/"
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)
        self.assertTrue(booking.penalty_applied)
