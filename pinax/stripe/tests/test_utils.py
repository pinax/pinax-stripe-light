import datetime
import decimal

from django.test import TestCase
from django.utils import timezone

from ..utils import (
    convert_amount_for_api,
    convert_amount_for_db,
    convert_tstamp,
    obfuscate_secret_key
)


class TestTimestampConversion(TestCase):

    def test_conversion_without_field_name(self):
        stamp = convert_tstamp(1365567407)
        self.assertEqual(
            stamp,
            datetime.datetime(2013, 4, 10, 4, 16, 47, tzinfo=timezone.utc)
        )

    def test_conversion_with_field_name(self):
        stamp = convert_tstamp({"my_date": 1365567407}, "my_date")
        self.assertEqual(
            stamp,
            datetime.datetime(2013, 4, 10, 4, 16, 47, tzinfo=timezone.utc)
        )

    def test_conversion_with_invalid_field_name(self):
        stamp = convert_tstamp({"my_date": 1365567407}, "foo")
        self.assertEqual(
            stamp,
            None
        )

    def test_conversion_with_field_name_but_none(self):
        stamp = convert_tstamp({"my_date": None}, "my_date")
        self.assertEqual(
            stamp,
            None
        )


class ConvertAmountForDBTests(TestCase):

    def test_convert_amount_for_db(self):
        expected = decimal.Decimal("9.99")
        actual = convert_amount_for_db(999)
        self.assertEqual(expected, actual)

    def test_convert_amount_for_db_zero_currency(self):
        expected = decimal.Decimal("999")
        actual = convert_amount_for_db(999, currency="jpy")
        self.assertEqual(expected, actual)

    def test_convert_amount_for_db_none_currency(self):
        expected = decimal.Decimal("9.99")
        actual = convert_amount_for_db(999, currency=None)
        self.assertEqual(expected, actual)


class ConvertAmountForApiTests(TestCase):

    def test_convert_amount_for_api(self):
        expected = 999
        actual = convert_amount_for_api(decimal.Decimal("9.99"))
        self.assertEqual(expected, actual)

    def test_convert_amount_for_api_zero_currency(self):
        expected = 999
        actual = convert_amount_for_api(decimal.Decimal("999"), currency="jpy")
        self.assertEqual(expected, actual)

    def test_convert_amount_for_api_none_currency(self):
        expected = 999
        actual = convert_amount_for_api(decimal.Decimal("9.99"), currency=None)
        self.assertEqual(expected, actual)


class OtherUtilTests(TestCase):
    def test_obfuscate_secret_key(self):
        val = obfuscate_secret_key("foobar")
        self.assertEqual(val, "********************obar")
