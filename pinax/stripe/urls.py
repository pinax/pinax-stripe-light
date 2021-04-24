from django.urls import path

from .views import Webhook

urlpatterns = [
    path("webhook/", Webhook.as_view(), name="pinax_stripe_webhook"),
]
