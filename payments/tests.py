import datetime
import os
import sys

from django.conf import settings


if not settings.configured:
    settings.configure(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:"
            }
        },
        # ROOT_URLCONF="payments.urls",
        INSTALLED_APPS=[
            "django.contrib.auth",
            "jsonfield",
            "payments"
        ],
        STRIPE_PUBLIC_KEY="",
        STRIPE_SECRET_KEY="",
        PAYMENTS_PLANS={}
    )


from django.test import TestCase
from django.utils import timezone

from .models import convert_tstamp


class TestTimestampConversion(TestCase):
    
    def test_conversion_without_field_name(self):
        stamp = convert_tstamp(1365567407)
        self.assertEquals(
            stamp,
            datetime.datetime(2013, 4, 10, 4, 16, 47, tzinfo=timezone.utc)
        )
    
    def test_conversion_with_field_name(self):
        stamp = convert_tstamp({"my_date": 1365567407}, "my_date")
        self.assertEquals(
            stamp,
            datetime.datetime(2013, 4, 10, 4, 16, 47, tzinfo=timezone.utc)
        )
    
    def test_conversion_with_invalid_field_name(self):
        stamp = convert_tstamp({"my_date": 1365567407}, "foo")
        self.assertEquals(
            stamp,
            None
        )