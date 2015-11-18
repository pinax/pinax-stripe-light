import datetime

from django.test import TestCase
from django.utils import timezone

from ..utils import convert_tstamp, plan_from_stripe_id


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

    def test_conversion_with_field_name_but_none(self):
        stamp = convert_tstamp({"my_date": None}, "my_date")
        self.assertEquals(
            stamp,
            None
        )


class TestPlanFromStripeId(TestCase):

    def test_plan_from_stripe_id_valid(self):
        self.assertEquals(
            plan_from_stripe_id("pro-monthly"),
            "pro"
        )

    def test_plan_from_stripe_id_invalid(self):
        self.assertIsNone(plan_from_stripe_id("invalide"))
