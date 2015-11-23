import decimal

from django.test import TestCase

from django.contrib.auth import get_user_model

from mock import patch

from ..actions import charges
from ..proxies import CustomerProxy, ChargeProxy


class ChargesTests(TestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        self.customer = CustomerProxy.objects.create(
            user=self.user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )

    def test_create_amount_not_decimal_raises_error(self):
        with self.assertRaises(ValueError):
            charges.create(customer=self.customer, amount=10)

    def test_create_source_and_customer_both_none_raises_error(self):
        with self.assertRaises(ValueError):
            charges.create(amount=decimal.Decimal("10"))

    @patch("pinax.stripe.actions.syncs.sync_charge_from_stripe_data")
    @patch("stripe.Charge.create")
    def test_create_send_receipt_false_skips_sending_receipt(self, CreateMock, SyncMock):
        ChargeMock = charges.create(amount=decimal.Decimal("10"), customer=self.customer, send_receipt=False)
        self.assertTrue(CreateMock.called)
        self.assertTrue(SyncMock.called)
        self.assertFalse(ChargeMock.send_receipt.called)

    @patch("pinax.stripe.actions.syncs.sync_charge_from_stripe_data")
    @patch("stripe.Charge.create")
    def test_create(self, CreateMock, SyncMock):
        ChargeMock = charges.create(amount=decimal.Decimal("10"), customer=self.customer)
        self.assertTrue(CreateMock.called)
        self.assertTrue(SyncMock.called)
        self.assertTrue(ChargeMock.send_receipt.called)

    @patch("pinax.stripe.actions.syncs.sync_charge_from_stripe_data")
    @patch("stripe.Charge.retrieve")
    def test_capture(self, RetrieveMock, SyncMock):
        charges.capture(ChargeProxy(amount=decimal.Decimal("100"), currency="usd"))
        self.assertTrue(RetrieveMock.return_value.capture.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.syncs.sync_charge_from_stripe_data")
    @patch("stripe.Charge.retrieve")
    def test_capture_with_amount(self, RetrieveMock, SyncMock):
        charges.capture(ChargeProxy(amount=decimal.Decimal("100"), currency="usd"), amount=decimal.Decimal("50"))
        self.assertTrue(RetrieveMock.return_value.capture.called)
        _, kwargs = RetrieveMock.return_value.capture.call_args
        self.assertEquals(kwargs["amount"], 5000)
        self.assertTrue(SyncMock.called)
