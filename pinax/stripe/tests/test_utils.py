import datetime
import decimal

from django.test import TestCase
from django.utils import timezone

from ..utils import convert_tstamp, convert_amount_for_api


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

    def test_jpy_amount_not_converted_to_cents(self):
        expected = 1000
        actual = convert_amount_for_api(decimal.Decimal("1000"), "jpy")
        self.assertEquals(expected, actual)

    def test_usd_amount_converted_to_cents(self):
        expected = 1000
        actual = convert_amount_for_api(decimal.Decimal("10.00"), "usd")
        self.assertEquals(expected, actual)
