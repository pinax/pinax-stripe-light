import decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from ..hooks import DefaultHookSet
from ..models import Charge, Customer


class HooksTestCase(TestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="patrick",
            email="paltman@example.com"
        )
        self.customer = Customer.objects.create(
            user=self.user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        self.hookset = DefaultHookSet()

    def test_adjust_subscription_quantity(self):
        new_qty = self.hookset.adjust_subscription_quantity(customer=None, plan=None, quantity=3)
        self.assertEquals(new_qty, 3)

    def test_adjust_subscription_quantity_none(self):
        new_qty = self.hookset.adjust_subscription_quantity(customer=None, plan=None, quantity=None)
        self.assertEquals(new_qty, 1)

    def test_trial_period(self):
        period = self.hookset.trial_period(self.user, "some plan")
        self.assertIsNone(period)

    def test_send_receipt(self):
        charge = Charge.objects.create(
            stripe_id="ch_XXXXXX",
            customer=self.customer,
            source="card_01",
            amount=decimal.Decimal("10.00"),
            currency="usd",
            paid=True,
            refunded=False,
            disputed=False,
            receipt_sent=False
        )
        self.hookset.send_receipt(charge)
        self.assertTrue(Charge.objects.get(pk=charge.pk).receipt_sent)

    def test_send_receipt_with_email(self):
        charge = Charge.objects.create(
            stripe_id="ch_XXXXXX",
            customer=self.customer,
            source="card_01",
            amount=decimal.Decimal("10.00"),
            currency="usd",
            paid=True,
            refunded=False,
            disputed=False,
            receipt_sent=False
        )
        self.hookset.send_receipt(charge, email="goose@topgun.com")
        self.assertTrue(Charge.objects.get(pk=charge.pk).receipt_sent)
        self.assertEqual(mail.outbox[0].to, ["goose@topgun.com"])

    def test_send_receipt_already_sent(self):
        charge = Charge.objects.create(
            stripe_id="ch_XXXXXX",
            customer=self.customer,
            source="card_01",
            amount=decimal.Decimal("10.00"),
            currency="usd",
            paid=True,
            refunded=False,
            disputed=False,
            receipt_sent=True
        )
        self.hookset.send_receipt(charge)
        self.assertTrue(Charge.objects.get(pk=charge.pk).receipt_sent)
