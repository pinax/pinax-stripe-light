from django.conf.urls import url

from .views import Webhook

urlpatterns = [
    url(r"^webhook/$", Webhook.as_view(), name="pinax_stripe_webhook"),
]
