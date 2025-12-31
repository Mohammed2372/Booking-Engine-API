from django.urls import path

from .views import StripeWebhookAPIView

urlpatterns = [
    path("webhook/", StripeWebhookAPIView.as_view(), name="stripe-webhook"),
]
