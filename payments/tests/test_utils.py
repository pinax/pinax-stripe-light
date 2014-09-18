import datetime

import six
from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from ..models import convert_tstamp
from .. import settings as app_settings


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
            app_settings.plan_from_stripe_id("pro-monthly"),
            "pro"
        )

    def test_plan_from_stripe_id_invalid(self):
        self.assertIsNone(app_settings.plan_from_stripe_id("invalide"))


class TrialPeriodCallbackSettingTest(TestCase):

    def setUp(self):
        self.old_setting = settings.PAYMENTS_TRIAL_PERIOD_FOR_USER_CALLBACK
        del settings.PAYMENTS_TRIAL_PERIOD_FOR_USER_CALLBACK
        six.moves.reload_module(app_settings)

    def tearDown(self):
        settings.PAYMENTS_TRIAL_PERIOD_FOR_USER_CALLBACK = self.old_setting

    def test_callback_is_none_when_not_set(self):
        from ..settings import TRIAL_PERIOD_FOR_USER_CALLBACK
        self.assertIsNone(TRIAL_PERIOD_FOR_USER_CALLBACK)
