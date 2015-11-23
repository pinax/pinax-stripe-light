import decimal

from django.test import TestCase

from django.contrib.auth import get_user_model

from mock import patch, PropertyMock, Mock

from ..actions import charges, customers
from ..proxies import CustomerProxy, ChargeProxy, PlanProxy


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


class CustomersTests(TestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        self.plan = PlanProxy.objects.create(
            stripe_id="p1",
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )

    @patch("stripe.Customer.retrieve")
    @patch("stripe.Customer.create")
    def test_customer_create_user_only(self, CreateMock, RetrieveMock):
        cu = CreateMock()
        cu.account_balance = 0
        cu.delinquent = False
        cu.default_source = "card_178Zqj2eZvKYlo2Cr2fUZZz7"
        cu.currency = "usd"
        cu.id = "cus_XXXXX"
        customer = customers.create(self.user)
        self.assertEqual(customer.user, self.user)
        self.assertEqual(customer.stripe_id, "cus_XXXXX")
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["email"], self.user.email)
        self.assertIsNone(kwargs["source"])
        self.assertIsNone(kwargs["plan"])
        self.assertIsNone(kwargs["trial_end"])

    @patch("stripe.Invoice.create")
    @patch("stripe.Customer.retrieve")
    @patch("stripe.Customer.create")
    def test_customer_create_user_with_plan(self, CreateMock, RetrieveMock, InvoiceMock):
        PlanProxy.objects.create(
            stripe_id="pro-monthly",
            name="Pro ($19.99/month)",
            amount=19.99,
            interval="monthly",
            interval_count=1,
            currency="usd"
        )
        type(InvoiceMock()).amount_due = PropertyMock(return_value=3)
        cu = CreateMock()
        cu.account_balance = 0
        cu.delinquent = False
        cu.default_source = "card_178Zqj2eZvKYlo2Cr2fUZZz7"
        cu.currency = "usd"
        cu.id = "cus_YYYYYYYYYYYYY"
        subscription = Mock()
        subscription.plan.id = "pro-monthly"
        subscription.current_period_start = 1348876800
        subscription.current_period_end = 1349876800
        subscription.canceled_at = 1349876800
        subscription.ended_at = 1349876800
        subscription.application_fee_percent = 0
        subscription.plan.amount = 9999
        subscription.plan.currency = "usd"
        subscription.status = "active"
        subscription.cancel_at_period_end = False
        subscription.start = 1348876800
        subscription.quantity = 1
        subscription.trial_start = 1348876800
        subscription.trial_end = 1349876800
        subscription.id = "su_YYYYYYYYYYYYY"
        cu.subscriptions.data = [subscription]
        rm = RetrieveMock()
        rm.id = "cus_YYYYYYYYYYYYY"
        rm.account_balance = 0
        rm.delinquent = False
        rm.default_source = "card_178Zqj2eZvKYlo2Cr2fUZZz7"
        rm.currency = "usd"
        rm.subscription.plan.id = "pro-monthly"
        rm.subscriptions.data = [subscription]
        customer = customers.create(self.user, card="token232323", plan=self.plan)
        self.assertEqual(customer.user, self.user)
        self.assertEqual(customer.stripe_id, "cus_YYYYYYYYYYYYY")
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["email"], self.user.email)
        self.assertEqual(kwargs["source"], "token232323")
        self.assertEqual(kwargs["plan"], self.plan)
        self.assertIsNotNone(kwargs["trial_end"])
        self.assertTrue(InvoiceMock.called)
        self.assertTrue(customer.subscription_set.all()[0].plan, "pro")
