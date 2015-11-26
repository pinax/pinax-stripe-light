import datetime
import decimal

from django.test import TestCase
from django.utils import timezone

from django.contrib.auth import get_user_model

import stripe

from mock import patch, Mock

from ..actions import charges, customers, events, invoices, refunds, sources, subscriptions, syncs
from ..proxies import BitcoinRecieverProxy, CustomerProxy, ChargeProxy, CardProxy, PlanProxy, EventProxy, InvoiceProxy, SubscriptionProxy


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
    def test_create_send_receipt_False_skips_sending_receipt(self, CreateMock, SyncMock):
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
        CreateMock.return_value = dict(id="cus_XXXXX")
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
        CreateMock.return_value = dict(id="cus_YYYYYYYYYYYYY")
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


class SourcesTests(TestCase):

    @patch("pinax.stripe.actions.syncs.sync_payment_source_from_stripe_data")
    def test_create_card(self, SyncMock):
        CustomerMock = Mock()
        sources.create_card(CustomerMock, token="token")
        self.assertTrue(CustomerMock.stripe_customer.sources.create.called)
        _, kwargs = CustomerMock.stripe_customer.sources.create.call_args
        self.assertEquals(kwargs["source"], "token")
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.syncs.sync_payment_source_from_stripe_data")
    def test_update_card(self, SyncMock):
        CustomerMock = Mock()
        SourceMock = CustomerMock.stripe_customer.sources.retrieve()
        sources.update_card(CustomerMock, "")
        self.assertTrue(CustomerMock.stripe_customer.sources.retrieve.called)
        self.assertTrue(SourceMock.save.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.syncs.sync_payment_source_from_stripe_data")
    def test_update_card_name_not_none(self, SyncMock):
        CustomerMock = Mock()
        SourceMock = CustomerMock.stripe_customer.sources.retrieve()
        sources.update_card(CustomerMock, "", name="My Visa")
        self.assertTrue(CustomerMock.stripe_customer.sources.retrieve.called)
        self.assertTrue(SourceMock.save.called)
        self.assertEquals(SourceMock.name, "My Visa")
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.syncs.sync_payment_source_from_stripe_data")
    def test_update_card_exp_month_not_none(self, SyncMock):
        CustomerMock = Mock()
        SourceMock = CustomerMock.stripe_customer.sources.retrieve()
        sources.update_card(CustomerMock, "", exp_month="My Visa")
        self.assertTrue(CustomerMock.stripe_customer.sources.retrieve.called)
        self.assertTrue(SourceMock.save.called)
        self.assertEquals(SourceMock.exp_month, "My Visa")
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.syncs.sync_payment_source_from_stripe_data")
    def test_update_card_exp_year_not_none(self, SyncMock):
        CustomerMock = Mock()
        SourceMock = CustomerMock.stripe_customer.sources.retrieve()
        sources.update_card(CustomerMock, "", exp_year="My Visa")
        self.assertTrue(CustomerMock.stripe_customer.sources.retrieve.called)
        self.assertTrue(SourceMock.save.called)
        self.assertEquals(SourceMock.exp_year, "My Visa")
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.syncs.sync_customer")
    def test_delete_card(self, SyncMock):
        CustomerMock = Mock()
        sources.delete_card(CustomerMock, source="token")
        self.assertTrue(CustomerMock.stripe_customer.sources.retrieve().delete.called)
        self.assertTrue(SyncMock.called)

    def test_delete_card_object(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        customer = CustomerProxy.objects.create(
            user=user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        card = CardProxy.objects.create(
            customer=customer,
            stripe_id="card_stripe",
            address_line_1_check="check",
            address_zip_check="check",
            country="us",
            cvc_check="check",
            exp_month=1,
            exp_year=2000,
            funding="funding",
            fingerprint="fingerprint"
        )
        pk = card.pk
        sources.delete_card_object("card_stripe")
        self.assertFalse(CardProxy.objects.filter(pk=pk).exists())

    def test_delete_card_object_not_card(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        customer = CustomerProxy.objects.create(
            user=user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        card = CardProxy.objects.create(
            customer=customer,
            stripe_id="bitcoin_stripe",
            address_line_1_check="check",
            address_zip_check="check",
            country="us",
            cvc_check="check",
            exp_month=1,
            exp_year=2000,
            funding="funding",
            fingerprint="fingerprint"
        )
        pk = card.pk
        sources.delete_card_object("bitcoin_stripe")
        self.assertTrue(CardProxy.objects.filter(pk=pk).exists())


class SubscriptionsTests(TestCase):

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

    def test_has_active_subscription(self):
        plan = PlanProxy.objects.create(
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )
        SubscriptionProxy.objects.create(
            customer=self.customer,
            plan=plan,
            quantity=1,
            start=timezone.now(),
            status="active",
            cancel_at_period_end=False
        )
        self.assertTrue(subscriptions.has_active_subscription(self.customer))

    def test_has_active_subscription_False_no_subscription(self):
        self.assertFalse(subscriptions.has_active_subscription(self.customer))

    def test_has_active_subscription_False_expired(self):
        plan = PlanProxy.objects.create(
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )
        SubscriptionProxy.objects.create(
            customer=self.customer,
            plan=plan,
            quantity=1,
            start=timezone.now(),
            status="active",
            cancel_at_period_end=False,
            ended_at=timezone.now() - datetime.timedelta(days=3)
        )
        self.assertFalse(subscriptions.has_active_subscription(self.customer))

    def test_has_active_subscription_ended_but_not_expired(self):
        plan = PlanProxy.objects.create(
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )
        SubscriptionProxy.objects.create(
            customer=self.customer,
            plan=plan,
            quantity=1,
            start=timezone.now(),
            status="active",
            cancel_at_period_end=False,
            ended_at=timezone.now() + datetime.timedelta(days=3)
        )
        self.assertTrue(subscriptions.has_active_subscription(self.customer))

    @patch("pinax.stripe.actions.syncs.sync_subscription_from_stripe_data")
    def test_cancel_subscription(self, SyncMock):
        SubMock = Mock()
        subscriptions.cancel(SubMock)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.syncs.sync_subscription_from_stripe_data")
    def test_update(self, SyncMock):
        SubMock = Mock()
        SubMock.customer = self.customer
        subscriptions.update(SubMock)
        self.assertTrue(SubMock.stripe_subscription.save.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.syncs.sync_subscription_from_stripe_data")
    def test_update_plan(self, SyncMock):
        SubMock = Mock()
        SubMock.customer = self.customer
        subscriptions.update(SubMock, plan="test_value")
        self.assertEquals(SubMock.stripe_subscription.plan, "test_value")
        self.assertTrue(SubMock.stripe_subscription.save.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.syncs.sync_subscription_from_stripe_data")
    def test_update_plan_quantity(self, SyncMock):
        SubMock = Mock()
        SubMock.customer = self.customer
        subscriptions.update(SubMock, quantity="test_value")
        self.assertEquals(SubMock.stripe_subscription.quantity, "test_value")
        self.assertTrue(SubMock.stripe_subscription.save.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.syncs.sync_subscription_from_stripe_data")
    def test_update_plan_prorate(self, SyncMock):
        SubMock = Mock()
        SubMock.customer = self.customer
        subscriptions.update(SubMock, prorate=False)
        self.assertEquals(SubMock.stripe_subscription.prorate, False)
        self.assertTrue(SubMock.stripe_subscription.save.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.syncs.sync_subscription_from_stripe_data")
    def test_update_plan_coupon(self, SyncMock):
        SubMock = Mock()
        SubMock.customer = self.customer
        subscriptions.update(SubMock, coupon="test_value")
        self.assertEquals(SubMock.stripe_subscription.coupon, "test_value")
        self.assertTrue(SubMock.stripe_subscription.save.called)
        self.assertTrue(SyncMock.called)

    @patch("stripe.Customer.retrieve")
    def test_subscription_create(self, CustomerMock):
        subscriptions.create(self.customer, "the-plan")
        sub_create = CustomerMock().subscriptions.create
        self.assertTrue(sub_create.called)

    @patch("stripe.Customer.retrieve")
    def test_subscription_create_with_trial(self, CustomerMock):
        subscriptions.create(self.customer, "the-plan", trial_days=3)
        sub_create = CustomerMock().subscriptions.create
        self.assertTrue(sub_create.called)
        _, kwargs = sub_create.call_args
        self.assertEquals(kwargs["trial_end"].date(), (datetime.datetime.utcnow() + datetime.timedelta(days=3)).date())

    @patch("stripe.Customer.retrieve")
    def test_subscription_create_token(self, CustomerMock):
        sub_create = CustomerMock().subscriptions.create
        subscriptions.create(self.customer, "the-plan", token="token")
        self.assertTrue(sub_create.called)
        _, kwargs = sub_create.call_args
        self.assertEquals(kwargs["source"], "token")


class SyncsTests(TestCase):

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

    @patch("stripe.Plan.all")
    def test_sync_plans(self, PlanAllMock):
        PlanAllMock().data = [
            {
                "id": "pro2",
                "object": "plan",
                "amount": 1999,
                "created": 1448121054,
                "currency": "usd",
                "interval": "month",
                "interval_count": 1,
                "livemode": False,
                "metadata": {},
                "name": "The Pro Plan",
                "statement_descriptor": "ALTMAN",
                "trial_period_days": 3
            },
            {
                "id": "simple1",
                "object": "plan",
                "amount": 999,
                "created": 1448121054,
                "currency": "usd",
                "interval": "month",
                "interval_count": 1,
                "livemode": False,
                "metadata": {},
                "name": "The Simple Plan",
                "statement_descriptor": "ALTMAN",
                "trial_period_days": 3
            },
        ]
        syncs.sync_plans()
        self.assertTrue(PlanProxy.objects.all().count(), 2)
        self.assertEquals(PlanProxy.objects.get(stripe_id="simple1").amount, decimal.Decimal("9.99"))

    @patch("stripe.Plan.all")
    def test_sync_plans_update(self, PlanAllMock):
        PlanAllMock().data = [
            {
                "id": "pro2",
                "object": "plan",
                "amount": 1999,
                "created": 1448121054,
                "currency": "usd",
                "interval": "month",
                "interval_count": 1,
                "livemode": False,
                "metadata": {},
                "name": "The Pro Plan",
                "statement_descriptor": "ALTMAN",
                "trial_period_days": 3
            },
            {
                "id": "simple1",
                "object": "plan",
                "amount": 999,
                "created": 1448121054,
                "currency": "usd",
                "interval": "month",
                "interval_count": 1,
                "livemode": False,
                "metadata": {},
                "name": "The Simple Plan",
                "statement_descriptor": "ALTMAN",
                "trial_period_days": 3
            },
        ]
        syncs.sync_plans()
        self.assertTrue(PlanProxy.objects.all().count(), 2)
        self.assertEquals(PlanProxy.objects.get(stripe_id="simple1").amount, decimal.Decimal("9.99"))
        PlanAllMock().data[1].update({"amount": 499})
        syncs.sync_plans()
        self.assertEquals(PlanProxy.objects.get(stripe_id="simple1").amount, decimal.Decimal("4.99"))

    def test_sync_payment_source_from_stripe_data_card(self):
        source = {
            "id": "card_17AMEBI10iPhvocM1LnJ0dBc",
            "object": "card",
            "address_city": None,
            "address_country": None,
            "address_line1": None,
            "address_line1_check": None,
            "address_line2": None,
            "address_state": None,
            "address_zip": None,
            "address_zip_check": None,
            "brand": "MasterCard",
            "country": "US",
            "customer": "cus_7PAYYALEwPuDJE",
            "cvc_check": "pass",
            "dynamic_last4": None,
            "exp_month": 10,
            "exp_year": 2018,
            "funding": "credit",
            "last4": "4444",
            "metadata": {
            },
            "name": None,
            "tokenization_method": None,
            "fingerprint": "xyz"
        }
        syncs.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertEquals(CardProxy.objects.get(stripe_id=source["id"]).exp_year, 2018)

    def test_sync_payment_source_from_stripe_data_card_updated(self):
        source = {
            "id": "card_17AMEBI10iPhvocM1LnJ0dBc",
            "object": "card",
            "address_city": None,
            "address_country": None,
            "address_line1": None,
            "address_line1_check": None,
            "address_line2": None,
            "address_state": None,
            "address_zip": None,
            "address_zip_check": None,
            "brand": "MasterCard",
            "country": "US",
            "customer": "cus_7PAYYALEwPuDJE",
            "cvc_check": "pass",
            "dynamic_last4": None,
            "exp_month": 10,
            "exp_year": 2018,
            "funding": "credit",
            "last4": "4444",
            "metadata": {
            },
            "name": None,
            "tokenization_method": None,
            "fingerprint": "xyz"
        }
        syncs.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertEquals(CardProxy.objects.get(stripe_id=source["id"]).exp_year, 2018)
        source.update({"exp_year": 2022})
        syncs.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertEquals(CardProxy.objects.get(stripe_id=source["id"]).exp_year, 2022)

    def test_sync_payment_source_from_stripe_data_bitcoin(self):
        source = {
            "id": "btcrcv_17BE32I10iPhvocMqViUU1w4",
            "object": "bitcoin_receiver",
            "active": False,
            "amount": 100,
            "amount_received": 0,
            "bitcoin_amount": 1757908,
            "bitcoin_amount_received": 0,
            "bitcoin_uri": "bitcoin:test_7i9Fo4b5wXcUAuoVBFrc7nc9HDxD1?amount=0.01757908",
            "created": 1448499344,
            "currency": "usd",
            "description": "Receiver for John Doe",
            "email": "test@example.com",
            "filled": False,
            "inbound_address": "test_7i9Fo4b5wXcUAuoVBFrc7nc9HDxD1",
            "livemode": False,
            "metadata": {
            },
            "refund_address": None,
            "uncaptured_funds": False,
            "used_for_payment": False
        }
        syncs.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertEquals(BitcoinRecieverProxy.objects.get(stripe_id=source["id"]).bitcoin_amount, 1757908)

    def test_sync_payment_source_from_stripe_data_bitcoin_updated(self):
        source = {
            "id": "btcrcv_17BE32I10iPhvocMqViUU1w4",
            "object": "bitcoin_receiver",
            "active": False,
            "amount": 100,
            "amount_received": 0,
            "bitcoin_amount": 1757908,
            "bitcoin_amount_received": 0,
            "bitcoin_uri": "bitcoin:test_7i9Fo4b5wXcUAuoVBFrc7nc9HDxD1?amount=0.01757908",
            "created": 1448499344,
            "currency": "usd",
            "description": "Receiver for John Doe",
            "email": "test@example.com",
            "filled": False,
            "inbound_address": "test_7i9Fo4b5wXcUAuoVBFrc7nc9HDxD1",
            "livemode": False,
            "metadata": {
            },
            "refund_address": None,
            "uncaptured_funds": False,
            "used_for_payment": False
        }
        syncs.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertEquals(BitcoinRecieverProxy.objects.get(stripe_id=source["id"]).bitcoin_amount, 1757908)
        source.update({"bitcoin_amount": 1886800})
        syncs.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertEquals(BitcoinRecieverProxy.objects.get(stripe_id=source["id"]).bitcoin_amount, 1886800)

    def test_sync_subscription_from_stripe_data(self):
        PlanProxy.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        subscription = {
            "id": "sub_7Q4BX0HMfqTpN8",
            "object": "subscription",
            "application_fee_percent": None,
            "cancel_at_period_end": False,
            "canceled_at": None,
            "current_period_end": 1448758544,
            "current_period_start": 1448499344,
            "customer": self.customer.stripe_id,
            "discount": None,
            "ended_at": None,
            "metadata": {
            },
            "plan": {
                "id": "pro2",
                "object": "plan",
                "amount": 1999,
                "created": 1448121054,
                "currency": "usd",
                "interval": "month",
                "interval_count": 1,
                "livemode": False,
                "metadata": {
                },
                "name": "The Pro Plan",
                "statement_descriptor": "ALTMAN",
                "trial_period_days": 3
            },
            "quantity": 1,
            "start": 1448499344,
            "status": "trialing",
            "tax_percent": None,
            "trial_end": 1448758544,
            "trial_start": 1448499344
        }
        syncs.sync_subscription_from_stripe_data(self.customer, subscription)
        self.assertEquals(SubscriptionProxy.objects.get(stripe_id=subscription["id"]).status, "trialing")

    def test_sync_subscription_from_stripe_data_updated(self):
        PlanProxy.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        subscription = {
            "id": "sub_7Q4BX0HMfqTpN8",
            "object": "subscription",
            "application_fee_percent": None,
            "cancel_at_period_end": False,
            "canceled_at": None,
            "current_period_end": 1448758544,
            "current_period_start": 1448499344,
            "customer": self.customer.stripe_id,
            "discount": None,
            "ended_at": None,
            "metadata": {
            },
            "plan": {
                "id": "pro2",
                "object": "plan",
                "amount": 1999,
                "created": 1448121054,
                "currency": "usd",
                "interval": "month",
                "interval_count": 1,
                "livemode": False,
                "metadata": {
                },
                "name": "The Pro Plan",
                "statement_descriptor": "ALTMAN",
                "trial_period_days": 3
            },
            "quantity": 1,
            "start": 1448499344,
            "status": "trialing",
            "tax_percent": None,
            "trial_end": 1448758544,
            "trial_start": 1448499344
        }
        syncs.sync_subscription_from_stripe_data(self.customer, subscription)
        self.assertEquals(SubscriptionProxy.objects.get(stripe_id=subscription["id"]).status, "trialing")
        subscription.update({"status": "active"})
        syncs.sync_subscription_from_stripe_data(self.customer, subscription)
        self.assertEquals(SubscriptionProxy.objects.get(stripe_id=subscription["id"]).status, "active")

    @patch("pinax.stripe.actions.syncs.sync_subscription_from_stripe_data")
    @patch("pinax.stripe.actions.syncs.sync_payment_source_from_stripe_data")
    @patch("stripe.Customer.retrieve")
    def test_sync_customer(self, RetreiveMock, SyncPaymentSourceMock, SyncSubscriptionMock):
        RetreiveMock.return_value = dict(
            account_balance=1999,
            currency="usd",
            delinquent=False,
            default_source=None,
            sources=dict(data=[Mock()]),
            subscriptions=dict(data=[Mock()])
        )
        syncs.sync_customer(self.customer)
        customer = CustomerProxy.objects.get(user=self.user)
        self.assertEquals(customer.account_balance, decimal.Decimal("19.99"))
        self.assertEquals(customer.currency, "usd")
        self.assertEquals(customer.delinquent, False)
        self.assertEquals(customer.default_source, "")
        self.assertTrue(SyncPaymentSourceMock.called)
        self.assertTrue(SyncSubscriptionMock.called)

    @patch("pinax.stripe.actions.syncs.sync_subscription_from_stripe_data")
    @patch("pinax.stripe.actions.syncs.sync_payment_source_from_stripe_data")
    def test_sync_customer_no_cu_provided(self, SyncPaymentSourceMock, SyncSubscriptionMock):
        cu = dict(
            account_balance=1999,
            currency="usd",
            delinquent=False,
            default_source=None,
            sources=dict(data=[Mock()]),
            subscriptions=dict(data=[Mock()])
        )
        syncs.sync_customer(self.customer, cu=cu)
        customer = CustomerProxy.objects.get(user=self.user)
        self.assertEquals(customer.account_balance, decimal.Decimal("19.99"))
        self.assertEquals(customer.currency, "usd")
        self.assertEquals(customer.delinquent, False)
        self.assertEquals(customer.default_source, "")
        self.assertTrue(SyncPaymentSourceMock.called)
        self.assertTrue(SyncSubscriptionMock.called)

    @patch("pinax.stripe.actions.syncs.sync_invoice_from_stripe_data")
    @patch("stripe.Customer.retrieve")
    def test_sync_invoices_for_customer(self, RetreiveMock, SyncMock):
        RetreiveMock().invoices().data = [Mock()]
        syncs.sync_invoices_for_customer(self.customer)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.syncs.sync_charge_from_stripe_data")
    @patch("stripe.Customer.retrieve")
    def test_sync_charges_for_customer(self, RetreiveMock, SyncMock):
        RetreiveMock().charges().data = [Mock()]
        syncs.sync_charges_for_customer(self.customer)
        self.assertTrue(SyncMock.called)

    def test_sync_charge_from_stripe_data(self):
        data = {
            "id": "ch_17A1dUI10iPhvocMOecpvQlI",
            "object": "charge",
            "amount": 200,
            "amount_refunded": 0,
            "application_fee": None,
            "balance_transaction": "txn_179l3zI10iPhvocMhvKxAer7",
            "captured": True,
            "created": 1448213304,
            "currency": "usd",
            "customer": self.customer.stripe_id,
            "description": None,
            "destination": None,
            "dispute": None,
            "failure_code": None,
            "failure_message": None,
            "fraud_details": {
            },
            "invoice": "in_17A1dUI10iPhvocMSGtIfUDF",
            "livemode": False,
            "metadata": {
            },
            "paid": True,
            "receipt_email": None,
            "receipt_number": None,
            "refunded": False,
            "refunds": {
                "object": "list",
                "data": [

                ],
                "has_more": False,
                "total_count": 0,
                "url": "/v1/charges/ch_17A1dUI10iPhvocMOecpvQlI/refunds"
            },
            "shipping": None,
            "source": {
                "id": "card_179o0lI10iPhvocMZgdPiR5M",
                "object": "card",
                "address_city": None,
                "address_country": None,
                "address_line1": None,
                "address_line1_check": None,
                "address_line2": None,
                "address_state": None,
                "address_zip": None,
                "address_zip_check": None,
                "brand": "Visa",
                "country": "US",
                "customer": "cus_7ObCqsp1NGVT6o",
                "cvc_check": None,
                "dynamic_last4": None,
                "exp_month": 10,
                "exp_year": 2019,
                "funding": "credit",
                "last4": "4242",
                "metadata": {
                },
                "name": None,
                "tokenization_method": None
            },
            "statement_descriptor": "A descriptor",
            "status": "succeeded"
        }
        syncs.sync_charge_from_stripe_data(data)
        charge = ChargeProxy.objects.get(customer=self.customer, stripe_id=data["id"])
        self.assertEquals(charge.amount, decimal.Decimal("2"))

    def test_sync_charge_from_stripe_data_description(self):
        data = {
            "id": "ch_17A1dUI10iPhvocMOecpvQlI",
            "object": "charge",
            "amount": 200,
            "amount_refunded": 0,
            "application_fee": None,
            "balance_transaction": "txn_179l3zI10iPhvocMhvKxAer7",
            "captured": True,
            "created": 1448213304,
            "currency": "usd",
            "customer": self.customer.stripe_id,
            "description": "This was a charge for awesome.",
            "destination": None,
            "dispute": None,
            "failure_code": None,
            "failure_message": None,
            "fraud_details": {
            },
            "invoice": "in_17A1dUI10iPhvocMSGtIfUDF",
            "livemode": False,
            "metadata": {
            },
            "paid": True,
            "receipt_email": None,
            "receipt_number": None,
            "refunded": False,
            "refunds": {
                "object": "list",
                "data": [

                ],
                "has_more": False,
                "total_count": 0,
                "url": "/v1/charges/ch_17A1dUI10iPhvocMOecpvQlI/refunds"
            },
            "shipping": None,
            "source": {
                "id": "card_179o0lI10iPhvocMZgdPiR5M",
                "object": "card",
                "address_city": None,
                "address_country": None,
                "address_line1": None,
                "address_line1_check": None,
                "address_line2": None,
                "address_state": None,
                "address_zip": None,
                "address_zip_check": None,
                "brand": "Visa",
                "country": "US",
                "customer": "cus_7ObCqsp1NGVT6o",
                "cvc_check": None,
                "dynamic_last4": None,
                "exp_month": 10,
                "exp_year": 2019,
                "funding": "credit",
                "last4": "4242",
                "metadata": {
                },
                "name": None,
                "tokenization_method": None
            },
            "statement_descriptor": "A descriptor",
            "status": "succeeded"
        }
        syncs.sync_charge_from_stripe_data(data)
        charge = ChargeProxy.objects.get(customer=self.customer, stripe_id=data["id"])
        self.assertEquals(charge.amount, decimal.Decimal("2"))
        self.assertEquals(charge.description, "This was a charge for awesome.")

    def test_sync_charge_from_stripe_data_amount_refunded(self):
        data = {
            "id": "ch_17A1dUI10iPhvocMOecpvQlI",
            "object": "charge",
            "amount": 200,
            "amount_refunded": 10000,
            "application_fee": None,
            "balance_transaction": "txn_179l3zI10iPhvocMhvKxAer7",
            "captured": True,
            "created": 1448213304,
            "currency": "usd",
            "customer": self.customer.stripe_id,
            "description": None,
            "destination": None,
            "dispute": None,
            "failure_code": None,
            "failure_message": None,
            "fraud_details": {
            },
            "invoice": "in_17A1dUI10iPhvocMSGtIfUDF",
            "livemode": False,
            "metadata": {
            },
            "paid": True,
            "receipt_email": None,
            "receipt_number": None,
            "refunded": False,
            "refunds": {
                "object": "list",
                "data": [

                ],
                "has_more": False,
                "total_count": 0,
                "url": "/v1/charges/ch_17A1dUI10iPhvocMOecpvQlI/refunds"
            },
            "shipping": None,
            "source": {
                "id": "card_179o0lI10iPhvocMZgdPiR5M",
                "object": "card",
                "address_city": None,
                "address_country": None,
                "address_line1": None,
                "address_line1_check": None,
                "address_line2": None,
                "address_state": None,
                "address_zip": None,
                "address_zip_check": None,
                "brand": "Visa",
                "country": "US",
                "customer": "cus_7ObCqsp1NGVT6o",
                "cvc_check": None,
                "dynamic_last4": None,
                "exp_month": 10,
                "exp_year": 2019,
                "funding": "credit",
                "last4": "4242",
                "metadata": {
                },
                "name": None,
                "tokenization_method": None
            },
            "statement_descriptor": "A descriptor",
            "status": "succeeded"
        }
        syncs.sync_charge_from_stripe_data(data)
        charge = ChargeProxy.objects.get(customer=self.customer, stripe_id=data["id"])
        self.assertEquals(charge.amount, decimal.Decimal("2"))
        self.assertEquals(charge.amount_refunded, decimal.Decimal("100"))

    def test_sync_charge_from_stripe_data_refunded(self):
        data = {
            "id": "ch_17A1dUI10iPhvocMOecpvQlI",
            "object": "charge",
            "amount": 200,
            "amount_refunded": 0,
            "application_fee": None,
            "balance_transaction": "txn_179l3zI10iPhvocMhvKxAer7",
            "captured": True,
            "created": 1448213304,
            "currency": "usd",
            "customer": self.customer.stripe_id,
            "description": None,
            "destination": None,
            "dispute": None,
            "failure_code": None,
            "failure_message": None,
            "fraud_details": {
            },
            "invoice": "in_17A1dUI10iPhvocMSGtIfUDF",
            "livemode": False,
            "metadata": {
            },
            "paid": True,
            "receipt_email": None,
            "receipt_number": None,
            "refunded": True,
            "refunds": {
                "object": "list",
                "data": [

                ],
                "has_more": False,
                "total_count": 0,
                "url": "/v1/charges/ch_17A1dUI10iPhvocMOecpvQlI/refunds"
            },
            "shipping": None,
            "source": {
                "id": "card_179o0lI10iPhvocMZgdPiR5M",
                "object": "card",
                "address_city": None,
                "address_country": None,
                "address_line1": None,
                "address_line1_check": None,
                "address_line2": None,
                "address_state": None,
                "address_zip": None,
                "address_zip_check": None,
                "brand": "Visa",
                "country": "US",
                "customer": "cus_7ObCqsp1NGVT6o",
                "cvc_check": None,
                "dynamic_last4": None,
                "exp_month": 10,
                "exp_year": 2019,
                "funding": "credit",
                "last4": "4242",
                "metadata": {
                },
                "name": None,
                "tokenization_method": None
            },
            "statement_descriptor": "A descriptor",
            "status": "succeeded"
        }
        syncs.sync_charge_from_stripe_data(data)
        charge = ChargeProxy.objects.get(customer=self.customer, stripe_id=data["id"])
        self.assertEquals(charge.amount, decimal.Decimal("2"))
        self.assertEquals(charge.refunded, True)

    @patch("stripe.Customer.retrieve")
    def test_retrieve_stripe_subscription(self, CustomerMock):
        CustomerMock().subscriptions.retrieve.return_value = "subscription"
        value = syncs._retrieve_stripe_subscription(self.customer, "sub id")
        self.assertEquals(value, "subscription")

    def test_retrieve_stripe_subscription_no_sub_id(self):
        value = syncs._retrieve_stripe_subscription(self.customer, None)
        self.assertIsNone(value)

    @patch("stripe.Customer.retrieve")
    def test_retrieve_stripe_subscription_missing_subscription(self, CustomerMock):
        CustomerMock().subscriptions.retrieve.side_effect = stripe.InvalidRequestError("does not have a subscription with ID", "error")
        value = syncs._retrieve_stripe_subscription(self.customer, "sub id")
        self.assertIsNone(value)

    @patch("stripe.Customer.retrieve")
    def test_retrieve_stripe_subscription_invalid_request(self, CustomerMock):
        CustomerMock().subscriptions.retrieve.side_effect = stripe.InvalidRequestError("Bad", "error")
        with self.assertRaises(stripe.InvalidRequestError):
            syncs._retrieve_stripe_subscription(self.customer, "sub id")

    def test_sync_invoice_items(self):
        plan = PlanProxy.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        subscription = SubscriptionProxy.objects.create(
            stripe_id="sub_7Q4BX0HMfqTpN8",
            customer=self.customer,
            plan=plan,
            quantity=1,
            status="active",
            start=timezone.now()
        )
        invoice = InvoiceProxy.objects.create(
            stripe_id="inv_001",
            customer=self.customer,
            amount_due=100,
            period_end=timezone.now(),
            period_start=timezone.now(),
            subtotal=100,
            total=100,
            date=timezone.now(),
            subscription=subscription
        )
        items = [{
            "id": subscription.stripe_id,
            "object": "line_item",
            "amount": 0,
            "currency": "usd",
            "description": None,
            "discountable": True,
            "livemode": True,
            "metadata": {
            },
            "period": {
                "start": 1448499344,
                "end": 1448758544
            },
            "plan": {
                "id": "pro2",
                "object": "plan",
                "amount": 1999,
                "created": 1448121054,
                "currency": "usd",
                "interval": "month",
                "interval_count": 1,
                "livemode": False,
                "metadata": {
                },
                "name": "The Pro Plan",
                "statement_descriptor": "ALTMAN",
                "trial_period_days": 3
            },
            "proration": False,
            "quantity": 1,
            "subscription": None,
            "type": "subscription"
        }]
        syncs._sync_invoice_items(invoice, items)
        self.assertTrue(invoice.items.all().count(), 1)

    def test_sync_invoice_items_no_plan(self):
        plan = PlanProxy.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        subscription = SubscriptionProxy.objects.create(
            stripe_id="sub_7Q4BX0HMfqTpN8",
            customer=self.customer,
            plan=plan,
            quantity=1,
            status="active",
            start=timezone.now()
        )
        invoice = InvoiceProxy.objects.create(
            stripe_id="inv_001",
            customer=self.customer,
            amount_due=100,
            period_end=timezone.now(),
            period_start=timezone.now(),
            subtotal=100,
            total=100,
            date=timezone.now(),
            subscription=subscription
        )
        items = [{
            "id": subscription.stripe_id,
            "object": "line_item",
            "amount": 0,
            "currency": "usd",
            "description": None,
            "discountable": True,
            "livemode": True,
            "metadata": {
            },
            "period": {
                "start": 1448499344,
                "end": 1448758544
            },
            "proration": False,
            "quantity": 1,
            "subscription": None,
            "type": "subscription"
        }]
        syncs._sync_invoice_items(invoice, items)
        self.assertTrue(invoice.items.all().count(), 1)
        self.assertEquals(invoice.items.all()[0].plan, plan)

    def test_sync_invoice_items_type_not_subscription(self):
        invoice = InvoiceProxy.objects.create(
            stripe_id="inv_001",
            customer=self.customer,
            amount_due=100,
            period_end=timezone.now(),
            period_start=timezone.now(),
            subtotal=100,
            total=100,
            date=timezone.now()
        )
        items = [{
            "id": "ii_23lkj2lkj",
            "object": "line_item",
            "amount": 2000,
            "currency": "usd",
            "description": "Something random",
            "discountable": True,
            "livemode": True,
            "metadata": {
            },
            "period": {
                "start": 1448499344,
                "end": 1448758544
            },
            "proration": False,
            "quantity": 1,
            "subscription": None,
            "type": "line_item"
        }]
        syncs._sync_invoice_items(invoice, items)
        self.assertTrue(invoice.items.all().count(), 1)
        self.assertEquals(invoice.items.all()[0].description, "Something random")
        self.assertEquals(invoice.items.all()[0].amount, decimal.Decimal("20"))

    @patch("pinax.stripe.actions.syncs._retrieve_stripe_subscription")
    @patch("pinax.stripe.actions.syncs.sync_subscription_from_stripe_data")
    def test_sync_invoice_items_different_stripe_id_than_invoice(self, SyncMock, RetrieveSubscriptionMock):  # two subscriptions on invoice?
        PlanProxy.objects.create(stripe_id="simple", interval="month", interval_count=1, amount=decimal.Decimal("9.99"))
        plan = PlanProxy.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        subscription = SubscriptionProxy.objects.create(
            stripe_id="sub_7Q4BX0HMfqTpN8",
            customer=self.customer,
            plan=plan,
            quantity=1,
            status="active",
            start=timezone.now()
        )
        invoice = InvoiceProxy.objects.create(
            stripe_id="inv_001",
            customer=self.customer,
            amount_due=100,
            period_end=timezone.now(),
            period_start=timezone.now(),
            subtotal=100,
            total=100,
            date=timezone.now(),
            subscription=subscription
        )
        SyncMock.return_value = subscription
        items = [{
            "id": subscription.stripe_id,
            "object": "line_item",
            "amount": 0,
            "currency": "usd",
            "description": None,
            "discountable": True,
            "livemode": True,
            "metadata": {
            },
            "period": {
                "start": 1448499344,
                "end": 1448758544
            },
            "plan": {
                "id": "pro2",
                "object": "plan",
                "amount": 1999,
                "created": 1448121054,
                "currency": "usd",
                "interval": "month",
                "interval_count": 1,
                "livemode": False,
                "metadata": {
                },
                "name": "The Pro Plan",
                "statement_descriptor": "ALTMAN",
                "trial_period_days": 3
            },
            "proration": False,
            "quantity": 1,
            "subscription": None,
            "type": "subscription"
        }, {
            "id": "sub_7Q4BX0HMfqTpN9",
            "object": "line_item",
            "amount": 0,
            "currency": "usd",
            "description": None,
            "discountable": True,
            "livemode": True,
            "metadata": {
            },
            "period": {
                "start": 1448499344,
                "end": 1448758544
            },
            "plan": {
                "id": "simple",
                "object": "plan",
                "amount": 999,
                "created": 1448121054,
                "currency": "usd",
                "interval": "month",
                "interval_count": 1,
                "livemode": False,
                "metadata": {
                },
                "name": "The Simple Plan",
                "statement_descriptor": "ALTMAN",
                "trial_period_days": 3
            },
            "proration": False,
            "quantity": 1,
            "subscription": None,
            "type": "subscription"
        }]
        syncs._sync_invoice_items(invoice, items)
        self.assertTrue(invoice.items.all().count(), 2)

    @patch("pinax.stripe.actions.syncs._retrieve_stripe_subscription")
    def test_sync_invoice_items_updating(self, RetrieveSubscriptionMock):
        RetrieveSubscriptionMock.return_value = None
        PlanProxy.objects.create(stripe_id="simple", interval="month", interval_count=1, amount=decimal.Decimal("9.99"))
        plan = PlanProxy.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        subscription = SubscriptionProxy.objects.create(
            stripe_id="sub_7Q4BX0HMfqTpN8",
            customer=self.customer,
            plan=plan,
            quantity=1,
            status="active",
            start=timezone.now()
        )
        invoice = InvoiceProxy.objects.create(
            stripe_id="inv_001",
            customer=self.customer,
            amount_due=100,
            period_end=timezone.now(),
            period_start=timezone.now(),
            subtotal=100,
            total=100,
            date=timezone.now(),
            subscription=subscription
        )
        items = [{
            "id": subscription.stripe_id,
            "object": "line_item",
            "amount": 0,
            "currency": "usd",
            "description": None,
            "discountable": True,
            "livemode": True,
            "metadata": {
            },
            "period": {
                "start": 1448499344,
                "end": 1448758544
            },
            "plan": {
                "id": "pro2",
                "object": "plan",
                "amount": 1999,
                "created": 1448121054,
                "currency": "usd",
                "interval": "month",
                "interval_count": 1,
                "livemode": False,
                "metadata": {
                },
                "name": "The Pro Plan",
                "statement_descriptor": "ALTMAN",
                "trial_period_days": 3
            },
            "proration": False,
            "quantity": 1,
            "subscription": None,
            "type": "subscription"
        }, {
            "id": "sub_7Q4BX0HMfqTpN9",
            "object": "line_item",
            "amount": 0,
            "currency": "usd",
            "description": None,
            "discountable": True,
            "livemode": True,
            "metadata": {
            },
            "period": {
                "start": 1448499344,
                "end": 1448758544
            },
            "plan": {
                "id": "simple",
                "object": "plan",
                "amount": 999,
                "created": 1448121054,
                "currency": "usd",
                "interval": "month",
                "interval_count": 1,
                "livemode": False,
                "metadata": {
                },
                "name": "The Simple Plan",
                "statement_descriptor": "ALTMAN",
                "trial_period_days": 3
            },
            "proration": False,
            "quantity": 1,
            "subscription": None,
            "type": "subscription"
        }]
        syncs._sync_invoice_items(invoice, items)
        self.assertTrue(invoice.items.all().count(), 2)
        items[1].update({"description": "This is your second subscription"})
        syncs._sync_invoice_items(invoice, items)
        self.assertTrue(invoice.items.all().count(), 2)
        self.assertEquals(invoice.items.all()[1].description, "This is your second subscription")

    @patch("pinax.stripe.actions.syncs._sync_invoice_items")
    @patch("pinax.stripe.actions.syncs._retrieve_stripe_subscription")
    def test_sync_invoice_from_stripe_data(self, RetrieveSubscriptionMock, SyncInvoiceItemsMock):
        pass

    @patch("pinax.stripe.actions.syncs._sync_invoice_items")
    @patch("pinax.stripe.actions.syncs._retrieve_stripe_subscription")
    def test_sync_invoice_from_stripe_data_no_charge(self, RetrieveSubscriptionMock, SyncInvoiceItemsMock):
        pass

    @patch("pinax.stripe.actions.syncs._sync_invoice_items")
    @patch("pinax.stripe.actions.syncs._retrieve_stripe_subscription")
    def test_sync_invoice_from_stripe_data_no_subscription(self, RetrieveSubscriptionMock, SyncInvoiceItemsMock):
        pass

    @patch("pinax.stripe.actions.syncs._sync_invoice_items")
    @patch("pinax.stripe.actions.syncs._retrieve_stripe_subscription")
    def test_sync_invoice_from_stripe_data_updated(self, RetrieveSubscriptionMock, SyncInvoiceItemsMock):
        pass
