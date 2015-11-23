import decimal

from django.test import TestCase

from django.contrib.auth import get_user_model

import stripe

from mock import patch, Mock

from ..actions import charges, customers, events, invoices, refunds
from ..proxies import CustomerProxy, ChargeProxy, PlanProxy, EventProxy


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

    def test_get_customer_for_user(self):
        expected = CustomerProxy.objects.create(stripe_id="x", user=self.user)
        actual = customers.get_customer_for_user(self.user)
        self.assertEquals(expected, actual)

    @patch("pinax.stripe.actions.syncs.sync_customer")
    @patch("stripe.Customer.retrieve")
    def test_set_default_source(self, RetrieveMock, SyncMock):
        customers.set_default_source(CustomerProxy(), "the source")
        self.assertEquals(RetrieveMock().default_source, "the source")
        self.assertTrue(RetrieveMock().save.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.syncs.sync_customer")
    @patch("stripe.Customer.create")
    def test_customer_create_user_only(self, CreateMock, SyncMock):
        cu = CreateMock()
        cu.id = "cus_XXXXX"
        customer = customers.create(self.user)
        self.assertEqual(customer.user, self.user)
        self.assertEqual(customer.stripe_id, "cus_XXXXX")
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["email"], self.user.email)
        self.assertIsNone(kwargs["source"])
        self.assertIsNone(kwargs["plan"])
        self.assertIsNone(kwargs["trial_end"])
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.invoices.create_and_pay")
    @patch("pinax.stripe.actions.syncs.sync_customer")
    @patch("stripe.Customer.create")
    def test_customer_create_user_with_plan(self, CreateMock, SyncMock, CreateAndPayMock):
        PlanProxy.objects.create(
            stripe_id="pro-monthly",
            name="Pro ($19.99/month)",
            amount=19.99,
            interval="monthly",
            interval_count=1,
            currency="usd"
        )
        cu = CreateMock()
        cu.id = "cus_YYYYYYYYYYYYY"
        customer = customers.create(self.user, card="token232323", plan=self.plan)
        self.assertEqual(customer.user, self.user)
        self.assertEqual(customer.stripe_id, "cus_YYYYYYYYYYYYY")
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["email"], self.user.email)
        self.assertEqual(kwargs["source"], "token232323")
        self.assertEqual(kwargs["plan"], self.plan)
        self.assertIsNotNone(kwargs["trial_end"])
        self.assertTrue(SyncMock.called)
        self.assertTrue(CreateAndPayMock.called)


class EventsTests(TestCase):

    def test_dupe_event_exists(self):
        EventProxy.objects.create(stripe_id="evt_003", kind="foo", livemode=True, webhook_message="{}", api_version="", request="", pending_webhooks=0)
        self.assertTrue(events.dupe_event_exists("evt_003"))

    @patch("pinax.stripe.webhooks.AccountUpdatedWebhook.process")
    def test_add_event(self, ProcessMock):
        events.add_event(stripe_id="evt_001", kind="account.updated", livemode=True, message={})
        event = EventProxy.objects.get(stripe_id="evt_001")
        self.assertEquals(event.kind, "account.updated")
        self.assertTrue(ProcessMock.called)

    def test_add_event_new_webhook_kind(self):
        events.add_event(stripe_id="evt_002", kind="patrick.got.coffee", livemode=True, message={})
        event = EventProxy.objects.get(stripe_id="evt_002")
        self.assertEquals(event.processed, False)
        self.assertIsNone(event.validated_message)


class InvoicesTests(TestCase):

    @patch("stripe.Invoice.create")
    def test_create(self, CreateMock):
        invoices.create(Mock())
        self.assertTrue(CreateMock.called)

    @patch("pinax.stripe.actions.syncs.sync_invoice_from_stripe_data")
    def test_pay(self, SyncMock):
        invoice = Mock()
        invoice.paid = False
        invoice.closed = False
        self.assertTrue(invoices.pay(invoice))
        self.assertTrue(invoice.stripe_invoice.pay.called)
        self.assertTrue(SyncMock.called)

    def test_pay_invoice_paid(self):
        invoice = Mock()
        invoice.paid = True
        invoice.closed = False
        self.assertFalse(invoices.pay(invoice))
        self.assertFalse(invoice.stripe_invoice.pay.called)

    def test_pay_invoice_closed(self):
        invoice = Mock()
        invoice.paid = False
        invoice.closed = True
        self.assertFalse(invoices.pay(invoice))
        self.assertFalse(invoice.stripe_invoice.pay.called)

    @patch("stripe.Invoice.create")
    def test_create_and_pay(self, CreateMock):
        invoice = CreateMock()
        invoice.amount_due = 100
        self.assertTrue(invoices.create_and_pay(Mock()))
        self.assertTrue(invoice.pay.called)

    @patch("stripe.Invoice.create")
    def test_create_and_pay_amount_due_0(self, CreateMock):
        invoice = CreateMock()
        invoice.amount_due = 0
        self.assertTrue(invoices.create_and_pay(Mock()))
        self.assertFalse(invoice.pay.called)

    @patch("stripe.Invoice.create")
    def test_create_and_pay_invalid_request_error(self, CreateMock):
        invoice = CreateMock()
        invoice.amount_due = 100
        invoice.pay.side_effect = stripe.InvalidRequestError("Bad", "error")
        self.assertFalse(invoices.create_and_pay(Mock()))
        self.assertTrue(invoice.pay.called)


class RefundsTests(TestCase):

    @patch("pinax.stripe.actions.syncs.sync_charge_from_stripe_data")
    @patch("stripe.Refund.create")
    def test_create_amount_none(self, RefundMock, SyncMock):
        refunds.create(Mock())
        self.assertTrue(RefundMock.called)
        _, kwargs = RefundMock.call_args
        self.assertFalse("amount" in kwargs)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.syncs.sync_charge_from_stripe_data")
    @patch("stripe.Refund.create")
    def test_create_with_amount(self, RefundMock, SyncMock):
        ChargeMock = Mock()
        ChargeMock.calculate_refund_amount.return_value = decimal.Decimal("10")
        refunds.create(ChargeMock, amount=decimal.Decimal("10"))
        self.assertTrue(RefundMock.called)
        _, kwargs = RefundMock.call_args
        self.assertTrue("amount" in kwargs)
        self.assertEquals(kwargs["amount"], 1000)
        self.assertTrue(SyncMock.called)
