import datetime
import decimal
from unittest import skipIf
import time

import django
from django.test import TestCase
from django.utils import timezone

from django.contrib.auth import get_user_model

import stripe

from mock import patch, Mock

from ..actions import charges, customers, events, invoices, plans, refunds, sources, subscriptions, transfers
from ..models import BitcoinReceiver, Customer, Charge, Card, Plan, Event, Invoice, Subscription, Transfer


class ChargesTests(TestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        self.customer = Customer.objects.create(
            user=self.user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )

    def test_calculate_refund_amount(self):
        charge = Charge(amount=decimal.Decimal("100"), amount_refunded=decimal.Decimal("50"))
        expected = decimal.Decimal("50")
        actual = charges.calculate_refund_amount(charge)
        self.assertEquals(expected, actual)

    def test_calculate_refund_amount_with_amount_under(self):
        charge = Charge(amount=decimal.Decimal("100"), amount_refunded=decimal.Decimal("50"))
        expected = decimal.Decimal("25")
        actual = charges.calculate_refund_amount(charge, amount=decimal.Decimal("25"))
        self.assertEquals(expected, actual)

    def test_calculate_refund_amount_with_amount_over(self):
        charge = Charge(amount=decimal.Decimal("100"), amount_refunded=decimal.Decimal("50"))
        expected = decimal.Decimal("50")
        actual = charges.calculate_refund_amount(charge, amount=decimal.Decimal("100"))
        self.assertEquals(expected, actual)

    def test_create_amount_not_decimal_raises_error(self):
        with self.assertRaises(ValueError):
            charges.create(customer=self.customer, amount=10)

    def test_create_no_customer_raises_error(self):
        with self.assertRaises(TypeError):
            charges.create(amount=decimal.Decimal("10"))

    @patch("pinax.stripe.hooks.hookset.send_receipt")
    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Charge.create")
    def test_create_send_receipt_False_skips_sending_receipt(self, CreateMock, SyncMock, SendReceiptMock):
        charges.create(amount=decimal.Decimal("10"), customer=self.customer, send_receipt=False)
        self.assertTrue(CreateMock.called)
        self.assertTrue(SyncMock.called)
        self.assertFalse(SendReceiptMock.called)

    @patch("pinax.stripe.hooks.hookset.send_receipt")
    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Charge.create")
    def test_create(self, CreateMock, SyncMock, SendReceiptMock):
        charges.create(amount=decimal.Decimal("10"), customer=self.customer)
        self.assertTrue(CreateMock.called)
        self.assertTrue(SyncMock.called)
        self.assertTrue(SendReceiptMock.called)

    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Charge.retrieve")
    def test_capture(self, RetrieveMock, SyncMock):
        charges.capture(Charge(amount=decimal.Decimal("100"), currency="usd"))
        self.assertTrue(RetrieveMock.return_value.capture.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Charge.retrieve")
    def test_capture_with_amount(self, RetrieveMock, SyncMock):
        charges.capture(Charge(amount=decimal.Decimal("100"), currency="usd"), amount=decimal.Decimal("50"))
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
        self.plan = Plan.objects.create(
            stripe_id="p1",
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )

    def test_get_customer_for_user(self):
        expected = Customer.objects.create(stripe_id="x", user=self.user)
        actual = customers.get_customer_for_user(self.user)
        self.assertEquals(expected, actual)

    def test_get_customer_for_user_not_exists(self):
        actual = customers.get_customer_for_user(self.user)
        self.assertIsNone(actual)

    @patch("pinax.stripe.actions.customers.sync_customer")
    @patch("stripe.Customer.retrieve")
    def test_set_default_source(self, RetrieveMock, SyncMock):
        customers.set_default_source(Customer(), "the source")
        self.assertEquals(RetrieveMock().default_source, "the source")
        self.assertTrue(RetrieveMock().save.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.customers.sync_customer")
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

    @patch("stripe.Customer.retrieve")
    @patch("stripe.Customer.create")
    def test_customer_create_user_duplicate(self, CreateMock, RetrieveMock):
        # Create an existing database customer for this user
        original = Customer.objects.create(user=self.user, stripe_id='cus_XXXXX')

        new_customer = Mock()
        RetrieveMock.return_value = new_customer

        # customers.Create will return a new customer instance
        CreateMock.return_value = dict(id="cus_YYYYY")
        customer = customers.create(self.user)

        # But only one customer will exist - the original one
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(customer.stripe_id, original.stripe_id)

        # Check that the customer hasn't been modified
        self.assertEqual(customer.user, self.user)
        self.assertEqual(customer.stripe_id, "cus_XXXXX")
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["email"], self.user.email)
        self.assertIsNone(kwargs["source"])
        self.assertIsNone(kwargs["plan"])
        self.assertIsNone(kwargs["trial_end"])

        # But a customer *was* created, retrieved, and then disposed of.
        RetrieveMock.assert_called_once_with("cus_YYYYY")
        new_customer.delete.assert_called_once()

    @patch("pinax.stripe.actions.invoices.create_and_pay")
    @patch("pinax.stripe.actions.customers.sync_customer")
    @patch("stripe.Customer.create")
    def test_customer_create_user_with_plan(self, CreateMock, SyncMock, CreateAndPayMock):
        Plan.objects.create(
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

    @patch("stripe.Customer.retrieve")
    def test_purge(self, RetrieveMock):
        customer = Customer.objects.create(
            user=self.user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        customers.purge(customer)
        self.assertTrue(RetrieveMock().delete.called)
        self.assertIsNone(Customer.objects.get(stripe_id=customer.stripe_id).user)
        self.assertIsNotNone(Customer.objects.get(stripe_id=customer.stripe_id).date_purged)

    @patch("stripe.Customer.retrieve")
    def test_purge_already_deleted(self, RetrieveMock):
        RetrieveMock().delete.side_effect = stripe.InvalidRequestError("No such customer:", "error")
        customer = Customer.objects.create(
            user=self.user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        customers.purge(customer)
        self.assertTrue(RetrieveMock().delete.called)
        self.assertIsNone(Customer.objects.get(stripe_id=customer.stripe_id).user)
        self.assertIsNotNone(Customer.objects.get(stripe_id=customer.stripe_id).date_purged)

    @patch("stripe.Customer.retrieve")
    def test_purge_already_some_other_error(self, RetrieveMock):
        RetrieveMock().delete.side_effect = stripe.InvalidRequestError("Bad", "error")
        customer = Customer.objects.create(
            user=self.user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        with self.assertRaises(stripe.InvalidRequestError):
            customers.purge(customer)
        self.assertTrue(RetrieveMock().delete.called)
        self.assertIsNotNone(Customer.objects.get(stripe_id=customer.stripe_id).user)
        self.assertIsNone(Customer.objects.get(stripe_id=customer.stripe_id).date_purged)

    def test_can_charge(self):
        customer = Customer(default_source="card_001")
        self.assertTrue(customers.can_charge(customer))

    def test_can_charge_false_purged(self):
        customer = Customer(default_source="card_001", date_purged=timezone.now())
        self.assertFalse(customers.can_charge(customer))

    def test_can_charge_false_no_default_source(self):
        customer = Customer()
        self.assertFalse(customers.can_charge(customer))

    def test_link_customer(self):
        Customer.objects.create(stripe_id="cu_123")
        message = dict(data=dict(object=dict(id="cu_123")))
        event = Event.objects.create(validated_message=message, kind="customer.created")
        customers.link_customer(event)
        self.assertEquals(event.customer.stripe_id, "cu_123")

    def test_link_customer_non_customer_event(self):
        Customer.objects.create(stripe_id="cu_123")
        message = dict(data=dict(object=dict(customer="cu_123")))
        event = Event.objects.create(validated_message=message, kind="invoice.created")
        customers.link_customer(event)
        self.assertEquals(event.customer.stripe_id, "cu_123")

    def test_link_customer_no_customer(self):
        Customer.objects.create(stripe_id="cu_123")
        message = dict(data=dict(object=dict()))
        event = Event.objects.create(validated_message=message, kind="transfer.created")
        customers.link_customer(event)
        self.assertIsNone(event.customer, "cu_123")

    def test_link_customer_does_not_exist(self):
        message = dict(data=dict(object=dict(id="cu_123")))
        event = Event.objects.create(validated_message=message, kind="customer.created")
        customers.link_customer(event)
        self.assertIsNone(event.customer)


class EventsTests(TestCase):

    def test_dupe_event_exists(self):
        Event.objects.create(stripe_id="evt_003", kind="foo", livemode=True, webhook_message="{}", api_version="", request="", pending_webhooks=0)
        self.assertTrue(events.dupe_event_exists("evt_003"))

    @patch("pinax.stripe.webhooks.AccountUpdatedWebhook.process")
    def test_add_event(self, ProcessMock):
        events.add_event(stripe_id="evt_001", kind="account.updated", livemode=True, message={})
        event = Event.objects.get(stripe_id="evt_001")
        self.assertEquals(event.kind, "account.updated")
        self.assertTrue(ProcessMock.called)

    def test_add_event_new_webhook_kind(self):
        events.add_event(stripe_id="evt_002", kind="patrick.got.coffee", livemode=True, message={})
        event = Event.objects.get(stripe_id="evt_002")
        self.assertEquals(event.processed, False)
        self.assertIsNone(event.validated_message)


class InvoicesTests(TestCase):

    @patch("stripe.Invoice.create")
    def test_create(self, CreateMock):
        invoices.create(Mock())
        self.assertTrue(CreateMock.called)

    @patch("pinax.stripe.actions.invoices.sync_invoice_from_stripe_data")
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

    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Refund.create")
    def test_create_amount_none(self, RefundMock, SyncMock):
        refunds.create(Mock())
        self.assertTrue(RefundMock.called)
        _, kwargs = RefundMock.call_args
        self.assertFalse("amount" in kwargs)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.charges.calculate_refund_amount")
    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Refund.create")
    def test_create_with_amount(self, RefundMock, SyncMock, CalcMock):
        ChargeMock = Mock()
        CalcMock.return_value = decimal.Decimal("10")
        refunds.create(ChargeMock, amount=decimal.Decimal("10"))
        self.assertTrue(RefundMock.called)
        _, kwargs = RefundMock.call_args
        self.assertTrue("amount" in kwargs)
        self.assertEquals(kwargs["amount"], 1000)
        self.assertTrue(SyncMock.called)


class SourcesTests(TestCase):

    @patch("pinax.stripe.actions.sources.sync_payment_source_from_stripe_data")
    def test_create_card(self, SyncMock):
        CustomerMock = Mock()
        result = sources.create_card(CustomerMock, token="token")
        self.assertTrue(result is not None)
        self.assertTrue(CustomerMock.stripe_customer.sources.create.called)
        _, kwargs = CustomerMock.stripe_customer.sources.create.call_args
        self.assertEquals(kwargs["source"], "token")
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.sources.sync_payment_source_from_stripe_data")
    def test_update_card(self, SyncMock):
        CustomerMock = Mock()
        SourceMock = CustomerMock.stripe_customer.sources.retrieve()
        result = sources.update_card(CustomerMock, "")
        self.assertTrue(result is not None)
        self.assertTrue(CustomerMock.stripe_customer.sources.retrieve.called)
        self.assertTrue(SourceMock.save.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.sources.sync_payment_source_from_stripe_data")
    def test_update_card_name_not_none(self, SyncMock):
        CustomerMock = Mock()
        SourceMock = CustomerMock.stripe_customer.sources.retrieve()
        sources.update_card(CustomerMock, "", name="My Visa")
        self.assertTrue(CustomerMock.stripe_customer.sources.retrieve.called)
        self.assertTrue(SourceMock.save.called)
        self.assertEquals(SourceMock.name, "My Visa")
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.sources.sync_payment_source_from_stripe_data")
    def test_update_card_exp_month_not_none(self, SyncMock):
        CustomerMock = Mock()
        SourceMock = CustomerMock.stripe_customer.sources.retrieve()
        sources.update_card(CustomerMock, "", exp_month="My Visa")
        self.assertTrue(CustomerMock.stripe_customer.sources.retrieve.called)
        self.assertTrue(SourceMock.save.called)
        self.assertEquals(SourceMock.exp_month, "My Visa")
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.sources.sync_payment_source_from_stripe_data")
    def test_update_card_exp_year_not_none(self, SyncMock):
        CustomerMock = Mock()
        SourceMock = CustomerMock.stripe_customer.sources.retrieve()
        sources.update_card(CustomerMock, "", exp_year="My Visa")
        self.assertTrue(CustomerMock.stripe_customer.sources.retrieve.called)
        self.assertTrue(SourceMock.save.called)
        self.assertEquals(SourceMock.exp_year, "My Visa")
        self.assertTrue(SyncMock.called)

    @skipIf(django.VERSION < (1, 9), "Only for django 1.9+")
    def test_delete_card_dj19(self):
        CustomerMock = Mock()
        result = sources.delete_card(CustomerMock, source="card_token")
        self.assertEqual(result, (0, {'pinax_stripe.Card': 0}))
        self.assertTrue(CustomerMock.stripe_customer.sources.retrieve().delete.called)

    @skipIf(django.VERSION >= (1, 9), "Only for django before 1.9")
    def test_delete_card(self):
        CustomerMock = Mock()
        result = sources.delete_card(CustomerMock, source="card_token")
        self.assertTrue(result is None)
        self.assertTrue(CustomerMock.stripe_customer.sources.retrieve().delete.called)

    def test_delete_card_object(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        customer = Customer.objects.create(
            user=user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        card = Card.objects.create(
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
        self.assertFalse(Card.objects.filter(pk=pk).exists())

    def test_delete_card_object_not_card(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        customer = Customer.objects.create(
            user=user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        card = Card.objects.create(
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
        self.assertTrue(Card.objects.filter(pk=pk).exists())


class SubscriptionsTests(TestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        self.customer = Customer.objects.create(
            user=self.user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )

    def test_has_active_subscription(self):
        plan = Plan.objects.create(
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )
        Subscription.objects.create(
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
        plan = Plan.objects.create(
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )
        Subscription.objects.create(
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
        plan = Plan.objects.create(
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )
        Subscription.objects.create(
            customer=self.customer,
            plan=plan,
            quantity=1,
            start=timezone.now(),
            status="active",
            cancel_at_period_end=False,
            ended_at=timezone.now() + datetime.timedelta(days=3)
        )
        self.assertTrue(subscriptions.has_active_subscription(self.customer))

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_cancel_subscription(self, SyncMock):
        SubMock = Mock()
        subscriptions.cancel(SubMock)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_update(self, SyncMock):
        SubMock = Mock()
        SubMock.customer = self.customer
        subscriptions.update(SubMock)
        self.assertTrue(SubMock.stripe_subscription.save.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_update_plan(self, SyncMock):
        SubMock = Mock()
        SubMock.customer = self.customer
        subscriptions.update(SubMock, plan="test_value")
        self.assertEquals(SubMock.stripe_subscription.plan, "test_value")
        self.assertTrue(SubMock.stripe_subscription.save.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_update_plan_quantity(self, SyncMock):
        SubMock = Mock()
        SubMock.customer = self.customer
        subscriptions.update(SubMock, quantity="test_value")
        self.assertEquals(SubMock.stripe_subscription.quantity, "test_value")
        self.assertTrue(SubMock.stripe_subscription.save.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_update_plan_prorate(self, SyncMock):
        SubMock = Mock()
        SubMock.customer = self.customer
        subscriptions.update(SubMock, prorate=False)
        self.assertEquals(SubMock.stripe_subscription.prorate, False)
        self.assertTrue(SubMock.stripe_subscription.save.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_update_plan_coupon(self, SyncMock):
        SubMock = Mock()
        SubMock.customer = self.customer
        subscriptions.update(SubMock, coupon="test_value")
        self.assertEquals(SubMock.stripe_subscription.coupon, "test_value")
        self.assertTrue(SubMock.stripe_subscription.save.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_update_plan_charge_now(self, SyncMock):
        SubMock = Mock()
        SubMock.customer = self.customer
        SubMock.stripe_subscription.trial_end = time.time() + 1000000.0

        subscriptions.update(SubMock, charge_immediately=True)
        self.assertEquals(SubMock.stripe_subscription.trial_end, 'now')
        self.assertTrue(SubMock.stripe_subscription.save.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_update_plan_charge_now_old_trial(self, SyncMock):
        trial_end = time.time() - 1000000.0
        SubMock = Mock()
        SubMock.customer = self.customer
        SubMock.stripe_subscription.trial_end = trial_end

        subscriptions.update(SubMock, charge_immediately=True)
        # Trial end date hasn't changed
        self.assertEquals(SubMock.stripe_subscription.trial_end, trial_end)
        self.assertTrue(SubMock.stripe_subscription.save.called)
        self.assertTrue(SyncMock.called)

    @patch("stripe.Customer.retrieve")
    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_subscription_create(self, SyncMock, CustomerMock):
        subscriptions.create(self.customer, "the-plan")
        sub_create = CustomerMock().subscriptions.create
        self.assertTrue(sub_create.called)
        self.assertTrue(SyncMock.called)

    @patch("stripe.Customer.retrieve")
    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_subscription_create_with_trial(self, SyncMock, CustomerMock):
        subscriptions.create(self.customer, "the-plan", trial_days=3)
        sub_create = CustomerMock().subscriptions.create
        self.assertTrue(sub_create.called)
        self.assertTrue(SyncMock.called)
        _, kwargs = sub_create.call_args
        self.assertEquals(kwargs["trial_end"].date(), (datetime.datetime.utcnow() + datetime.timedelta(days=3)).date())

    @patch("stripe.Customer.retrieve")
    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_subscription_create_token(self, SyncMock, CustomerMock):
        sub_create = CustomerMock().subscriptions.create
        subscriptions.create(self.customer, "the-plan", token="token")
        self.assertTrue(sub_create.called)
        self.assertTrue(SyncMock.called)
        _, kwargs = sub_create.call_args
        self.assertEquals(kwargs["source"], "token")

    def test_is_period_current(self):
        sub = Subscription(current_period_end=(timezone.now() + datetime.timedelta(days=2)))
        self.assertTrue(subscriptions.is_period_current(sub))

    def test_is_period_current_false(self):
        sub = Subscription(current_period_end=(timezone.now() - datetime.timedelta(days=2)))
        self.assertFalse(subscriptions.is_period_current(sub))

    def test_is_status_current(self):
        sub = Subscription(status="trialing")
        self.assertTrue(subscriptions.is_status_current(sub))

    def test_is_status_current_false(self):
        sub = Subscription(status="canceled")
        self.assertFalse(subscriptions.is_status_current(sub))

    def test_is_valid(self):
        sub = Subscription(status="trialing")
        self.assertTrue(subscriptions.is_valid(sub))

    def test_is_valid_false(self):
        sub = Subscription(status="canceled")
        self.assertFalse(subscriptions.is_valid(sub))

    def test_is_valid_false_canceled(self):
        sub = Subscription(status="trialing", cancel_at_period_end=True, current_period_end=(timezone.now() - datetime.timedelta(days=2)))
        self.assertFalse(subscriptions.is_valid(sub))


class SyncsTests(TestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        self.customer = Customer.objects.create(
            user=self.user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )

    @patch("stripe.Plan.all")
    @patch("stripe.Plan.auto_paging_iter", create=True, side_effect=AttributeError)
    def test_sync_plans_deprecated(self, PlanAutoPagerMock, PlanAllMock):
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
        plans.sync_plans()
        self.assertTrue(Plan.objects.all().count(), 2)
        self.assertEquals(Plan.objects.get(stripe_id="simple1").amount, decimal.Decimal("9.99"))

    @patch("stripe.Plan.auto_paging_iter", create=True)
    def test_sync_plans(self, PlanAutoPagerMock):
        PlanAutoPagerMock.return_value = [
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
        plans.sync_plans()
        self.assertTrue(Plan.objects.all().count(), 2)
        self.assertEquals(Plan.objects.get(stripe_id="simple1").amount, decimal.Decimal("9.99"))

    @patch("stripe.Plan.auto_paging_iter", create=True)
    def test_sync_plans_update(self, PlanAutoPagerMock):
        PlanAutoPagerMock.return_value = [
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
        plans.sync_plans()
        self.assertTrue(Plan.objects.all().count(), 2)
        self.assertEquals(Plan.objects.get(stripe_id="simple1").amount, decimal.Decimal("9.99"))
        PlanAutoPagerMock.return_value[1].update({"amount": 499})
        plans.sync_plans()
        self.assertEquals(Plan.objects.get(stripe_id="simple1").amount, decimal.Decimal("4.99"))

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
        sources.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertEquals(Card.objects.get(stripe_id=source["id"]).exp_year, 2018)

    def test_sync_payment_source_from_stripe_data_card_blank_cvc_check(self):
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
            "cvc_check": None,
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
        sources.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertEquals(Card.objects.get(stripe_id=source["id"]).cvc_check, "")

    def test_sync_payment_source_from_stripe_data_card_blank_country(self):
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
            "country": None,
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
        sources.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertEquals(Card.objects.get(stripe_id=source["id"]).country, "")

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
        sources.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertEquals(Card.objects.get(stripe_id=source["id"]).exp_year, 2018)
        source.update({"exp_year": 2022})
        sources.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertEquals(Card.objects.get(stripe_id=source["id"]).exp_year, 2022)

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
        sources.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertEquals(BitcoinReceiver.objects.get(stripe_id=source["id"]).bitcoin_amount, 1757908)

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
        sources.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertEquals(BitcoinReceiver.objects.get(stripe_id=source["id"]).bitcoin_amount, 1757908)
        source.update({"bitcoin_amount": 1886800})
        sources.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertEquals(BitcoinReceiver.objects.get(stripe_id=source["id"]).bitcoin_amount, 1886800)

    def test_sync_subscription_from_stripe_data(self):
        Plan.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
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
        subscriptions.sync_subscription_from_stripe_data(self.customer, subscription)
        self.assertEquals(Subscription.objects.get(stripe_id=subscription["id"]).status, "trialing")

    def test_sync_subscription_from_stripe_data_updated(self):
        Plan.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
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
        subscriptions.sync_subscription_from_stripe_data(self.customer, subscription)
        self.assertEquals(Subscription.objects.get(stripe_id=subscription["id"]).status, "trialing")
        subscription.update({"status": "active"})
        subscriptions.sync_subscription_from_stripe_data(self.customer, subscription)
        self.assertEquals(Subscription.objects.get(stripe_id=subscription["id"]).status, "active")

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("pinax.stripe.actions.sources.sync_payment_source_from_stripe_data")
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
        customers.sync_customer(self.customer)
        customer = Customer.objects.get(user=self.user)
        self.assertEquals(customer.account_balance, decimal.Decimal("19.99"))
        self.assertEquals(customer.currency, "usd")
        self.assertEquals(customer.delinquent, False)
        self.assertEquals(customer.default_source, "")
        self.assertTrue(SyncPaymentSourceMock.called)
        self.assertTrue(SyncSubscriptionMock.called)

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("pinax.stripe.actions.sources.sync_payment_source_from_stripe_data")
    def test_sync_customer_no_cu_provided(self, SyncPaymentSourceMock, SyncSubscriptionMock):
        cu = dict(
            account_balance=1999,
            currency="usd",
            delinquent=False,
            default_source=None,
            sources=dict(data=[Mock()]),
            subscriptions=dict(data=[Mock()])
        )
        customers.sync_customer(self.customer, cu=cu)
        customer = Customer.objects.get(user=self.user)
        self.assertEquals(customer.account_balance, decimal.Decimal("19.99"))
        self.assertEquals(customer.currency, "usd")
        self.assertEquals(customer.delinquent, False)
        self.assertEquals(customer.default_source, "")
        self.assertTrue(SyncPaymentSourceMock.called)
        self.assertTrue(SyncSubscriptionMock.called)

    @patch("pinax.stripe.actions.invoices.sync_invoice_from_stripe_data")
    @patch("stripe.Customer.retrieve")
    def test_sync_invoices_for_customer(self, RetreiveMock, SyncMock):
        RetreiveMock().invoices().data = [Mock()]
        invoices.sync_invoices_for_customer(self.customer)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Customer.retrieve")
    def test_sync_charges_for_customer(self, RetreiveMock, SyncMock):
        RetreiveMock().charges().data = [Mock()]
        charges.sync_charges_for_customer(self.customer)
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
        charges.sync_charge_from_stripe_data(data)
        charge = Charge.objects.get(customer=self.customer, stripe_id=data["id"])
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
        charges.sync_charge_from_stripe_data(data)
        charge = Charge.objects.get(customer=self.customer, stripe_id=data["id"])
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
        charges.sync_charge_from_stripe_data(data)
        charge = Charge.objects.get(customer=self.customer, stripe_id=data["id"])
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
        charges.sync_charge_from_stripe_data(data)
        charge = Charge.objects.get(customer=self.customer, stripe_id=data["id"])
        self.assertEquals(charge.amount, decimal.Decimal("2"))
        self.assertEquals(charge.refunded, True)

    def test_sync_charge_from_stripe_data_failed(self):
        data = {
            "id": "ch_xxxxxxxxxxxxxxxxxxxxxxxx",
            "object": "charge",
            "amount": 200,
            "amount_refunded": 0,
            "application": None,
            "application_fee": None,
            "balance_transaction": None,
            "captured": False,
            "created": 1488208611,
            "currency": "usd",
            "customer": None,
            "description": None,
            "destination": None,
            "dispute": None,
            "failure_code": "card_declined",
            "failure_message": "Your card was declined.",
            "fraud_details": {},
            "invoice": None,
            "livemode": False,
            "metadata": {},
            "on_behalf_of": None,
            "order": None,
            "outcome": {
                "network_status": "declined_by_network",
                "reason": "generic_decline",
                "risk_level": "normal",
                "seller_message": "The bank did not return any further details with this decline.",
                "type": "issuer_declined"
            },
            "paid": False,
            "receipt_email": None,
            "receipt_number": None,
            "refunded": False,
            "refunds": {
                "object": "list",
                "data": [],
                "has_more": False,
                "total_count": 0,
                "url": "/v1/charges/ch_xxxxxxxxxxxxxxxxxxxxxxxx/refunds"
            },
            "review": None,
            "shipping": None,
            "source": {
                "id": "card_xxxxxxxxxxxxxxxxxxxxxxxx",
                "object": "card",
                "address_city": None,
                "address_country": None,
                "address_line1": None,
                "address_line1_check": None,
                "address_line2": None,
                "address_state": None,
                "address_zip": "424",
                "address_zip_check": "pass",
                "brand": "Visa",
                "country": "US",
                "customer": None,
                "cvc_check": "pass",
                "dynamic_last4": None,
                "exp_month": 4,
                "exp_year": 2024,
                "fingerprint": "xxxxxxxxxxxxxxxx",
                "funding": "credit",
                "last4": "0341",
                "metadata": {},
                "name": "example@example.com",
                "tokenization_method": None
            },
            "source_transfer": None,
            "statement_descriptor": None,
            "status": "failed",
            "transfer_group": None
        }
        charges.sync_charge_from_stripe_data(data)
        charge = Charge.objects.get(stripe_id=data["id"])
        self.assertEqual(charge.amount, decimal.Decimal("2"))
        self.assertEqual(charge.customer, None)

    @patch("stripe.Customer.retrieve")
    def test_retrieve_stripe_subscription(self, CustomerMock):
        CustomerMock().subscriptions.retrieve.return_value = "subscription"
        value = subscriptions.retrieve(self.customer, "sub id")
        self.assertEquals(value, "subscription")

    def test_retrieve_stripe_subscription_no_sub_id(self):
        value = subscriptions.retrieve(self.customer, None)
        self.assertIsNone(value)

    @patch("stripe.Customer.retrieve")
    def test_retrieve_stripe_subscription_missing_subscription(self, CustomerMock):
        CustomerMock().subscriptions.retrieve.side_effect = stripe.InvalidRequestError("does not have a subscription with ID", "error")
        value = subscriptions.retrieve(self.customer, "sub id")
        self.assertIsNone(value)

    @patch("stripe.Customer.retrieve")
    def test_retrieve_stripe_subscription_invalid_request(self, CustomerMock):
        CustomerMock().subscriptions.retrieve.side_effect = stripe.InvalidRequestError("Bad", "error")
        with self.assertRaises(stripe.InvalidRequestError):
            subscriptions.retrieve(self.customer, "sub id")

    def test_sync_invoice_items(self):
        plan = Plan.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        subscription = Subscription.objects.create(
            stripe_id="sub_7Q4BX0HMfqTpN8",
            customer=self.customer,
            plan=plan,
            quantity=1,
            status="active",
            start=timezone.now()
        )
        invoice = Invoice.objects.create(
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
        invoices.sync_invoice_items(invoice, items)
        self.assertTrue(invoice.items.all().count(), 1)

    def test_sync_invoice_items_no_plan(self):
        plan = Plan.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        subscription = Subscription.objects.create(
            stripe_id="sub_7Q4BX0HMfqTpN8",
            customer=self.customer,
            plan=plan,
            quantity=1,
            status="active",
            start=timezone.now()
        )
        invoice = Invoice.objects.create(
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
        invoices.sync_invoice_items(invoice, items)
        self.assertTrue(invoice.items.all().count(), 1)
        self.assertEquals(invoice.items.all()[0].plan, plan)

    def test_sync_invoice_items_type_not_subscription(self):
        invoice = Invoice.objects.create(
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
        invoices.sync_invoice_items(invoice, items)
        self.assertTrue(invoice.items.all().count(), 1)
        self.assertEquals(invoice.items.all()[0].description, "Something random")
        self.assertEquals(invoice.items.all()[0].amount, decimal.Decimal("20"))

    @patch("pinax.stripe.actions.subscriptions.retrieve")
    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_sync_invoice_items_different_stripe_id_than_invoice(self, SyncMock, RetrieveSubscriptionMock):  # two subscriptions on invoice?
        Plan.objects.create(stripe_id="simple", interval="month", interval_count=1, amount=decimal.Decimal("9.99"))
        plan = Plan.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        subscription = Subscription.objects.create(
            stripe_id="sub_7Q4BX0HMfqTpN8",
            customer=self.customer,
            plan=plan,
            quantity=1,
            status="active",
            start=timezone.now()
        )
        invoice = Invoice.objects.create(
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
        invoices.sync_invoice_items(invoice, items)
        self.assertTrue(invoice.items.all().count(), 2)

    @patch("pinax.stripe.actions.subscriptions.retrieve")
    def test_sync_invoice_items_updating(self, RetrieveSubscriptionMock):
        RetrieveSubscriptionMock.return_value = None
        Plan.objects.create(stripe_id="simple", interval="month", interval_count=1, amount=decimal.Decimal("9.99"))
        plan = Plan.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        subscription = Subscription.objects.create(
            stripe_id="sub_7Q4BX0HMfqTpN8",
            customer=self.customer,
            plan=plan,
            quantity=1,
            status="active",
            start=timezone.now()
        )
        invoice = Invoice.objects.create(
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
        invoices.sync_invoice_items(invoice, items)
        self.assertTrue(invoice.items.all().count(), 2)
        items[1].update({"description": "This is your second subscription"})
        invoices.sync_invoice_items(invoice, items)
        self.assertTrue(invoice.items.all().count(), 2)
        self.assertEquals(invoice.items.all()[1].description, "This is your second subscription")

    @patch("pinax.stripe.hooks.hookset.send_receipt")
    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("stripe.Charge.retrieve")
    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("pinax.stripe.actions.invoices.sync_invoice_items")
    @patch("pinax.stripe.actions.subscriptions.retrieve")
    def test_sync_invoice_from_stripe_data(self, RetrieveSubscriptionMock, SyncInvoiceItemsMock, SyncChargeMock, ChargeFetchMock, SyncSubscriptionMock, SendReceiptMock):
        plan = Plan.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        subscription = Subscription.objects.create(
            stripe_id="sub_7Q4BX0HMfqTpN8",
            customer=self.customer,
            plan=plan,
            quantity=1,
            status="active",
            start=timezone.now()
        )
        charge = Charge.objects.create(
            stripe_id="ch_XXXXXX",
            customer=self.customer,
            source="card_01",
            amount=decimal.Decimal("10.00"),
            currency="usd",
            paid=True,
            refunded=False,
            disputed=False
        )
        SyncChargeMock.return_value = charge
        SyncSubscriptionMock.return_value = subscription
        data = {
            "id": "in_17B6e8I10iPhvocMGtYd4hDD",
            "object": "invoice",
            "amount_due": 1999,
            "application_fee": None,
            "attempt_count": 0,
            "attempted": False,
            "charge": charge.stripe_id,
            "closed": False,
            "currency": "usd",
            "customer": self.customer.stripe_id,
            "date": 1448470892,
            "description": None,
            "discount": None,
            "ending_balance": None,
            "forgiven": False,
            "lines": {
                "data": [{
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
                }],
                "total_count": 1,
                "object": "list",
                "url": "/v1/invoices/in_17B6e8I10iPhvocMGtYd4hDD/lines"
            },
            "livemode": False,
            "metadata": {
            },
            "next_payment_attempt": 1448474492,
            "paid": False,
            "period_end": 1448470739,
            "period_start": 1448211539,
            "receipt_number": None,
            "starting_balance": 0,
            "statement_descriptor": None,
            "subscription": subscription.stripe_id,
            "subtotal": 1999,
            "tax": None,
            "tax_percent": None,
            "total": 1999,
            "webhooks_delivered_at": None
        }
        invoices.sync_invoice_from_stripe_data(data)
        self.assertTrue(SyncInvoiceItemsMock.called)
        self.assertEquals(Invoice.objects.filter(customer=self.customer).count(), 1)
        self.assertTrue(ChargeFetchMock.called)
        self.assertTrue(SyncChargeMock.called)
        self.assertTrue(SendReceiptMock.called)

    @patch("pinax.stripe.hooks.hookset.send_receipt")
    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("stripe.Charge.retrieve")
    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("pinax.stripe.actions.invoices.sync_invoice_items")
    @patch("pinax.stripe.actions.subscriptions.retrieve")
    def test_sync_invoice_from_stripe_data_no_send_receipt(self, RetrieveSubscriptionMock, SyncInvoiceItemsMock, SyncChargeMock, ChargeFetchMock, SyncSubscriptionMock, SendReceiptMock):
        plan = Plan.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        subscription = Subscription.objects.create(
            stripe_id="sub_7Q4BX0HMfqTpN8",
            customer=self.customer,
            plan=plan,
            quantity=1,
            status="active",
            start=timezone.now()
        )
        charge = Charge.objects.create(
            stripe_id="ch_XXXXXX",
            customer=self.customer,
            source="card_01",
            amount=decimal.Decimal("10.00"),
            currency="usd",
            paid=True,
            refunded=False,
            disputed=False
        )
        SyncChargeMock.return_value = charge
        SyncSubscriptionMock.return_value = subscription
        data = {
            "id": "in_17B6e8I10iPhvocMGtYd4hDD",
            "object": "invoice",
            "amount_due": 1999,
            "application_fee": None,
            "attempt_count": 0,
            "attempted": False,
            "charge": charge.stripe_id,
            "closed": False,
            "currency": "usd",
            "customer": self.customer.stripe_id,
            "date": 1448470892,
            "description": None,
            "discount": None,
            "ending_balance": None,
            "forgiven": False,
            "lines": {
                "data": [{
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
                }],
                "total_count": 1,
                "object": "list",
                "url": "/v1/invoices/in_17B6e8I10iPhvocMGtYd4hDD/lines"
            },
            "livemode": False,
            "metadata": {
            },
            "next_payment_attempt": 1448474492,
            "paid": False,
            "period_end": 1448470739,
            "period_start": 1448211539,
            "receipt_number": None,
            "starting_balance": 0,
            "statement_descriptor": None,
            "subscription": subscription.stripe_id,
            "subtotal": 1999,
            "tax": None,
            "tax_percent": None,
            "total": 1999,
            "webhooks_delivered_at": None
        }
        invoices.sync_invoice_from_stripe_data(data, send_receipt=False)
        self.assertTrue(SyncInvoiceItemsMock.called)
        self.assertEquals(Invoice.objects.filter(customer=self.customer).count(), 1)
        self.assertTrue(ChargeFetchMock.called)
        self.assertTrue(SyncChargeMock.called)
        self.assertFalse(SendReceiptMock.called)

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("pinax.stripe.actions.invoices.sync_invoice_items")
    @patch("pinax.stripe.actions.subscriptions.retrieve")
    def test_sync_invoice_from_stripe_data_no_charge(self, RetrieveSubscriptionMock, SyncInvoiceItemsMock, SyncSubscriptionMock):
        plan = Plan.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        subscription = Subscription.objects.create(
            stripe_id="sub_7Q4BX0HMfqTpN8",
            customer=self.customer,
            plan=plan,
            quantity=1,
            status="active",
            start=timezone.now()
        )
        SyncSubscriptionMock.return_value = subscription
        data = {
            "id": "in_17B6e8I10iPhvocMGtYd4hDD",
            "object": "invoice",
            "amount_due": 1999,
            "application_fee": None,
            "attempt_count": 0,
            "attempted": False,
            "charge": None,
            "closed": False,
            "currency": "usd",
            "customer": self.customer.stripe_id,
            "date": 1448470892,
            "description": None,
            "discount": None,
            "ending_balance": None,
            "forgiven": False,
            "lines": {
                "data": [{
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
                }],
                "total_count": 1,
                "object": "list",
                "url": "/v1/invoices/in_17B6e8I10iPhvocMGtYd4hDD/lines"
            },
            "livemode": False,
            "metadata": {
            },
            "next_payment_attempt": 1448474492,
            "paid": False,
            "period_end": 1448470739,
            "period_start": 1448211539,
            "receipt_number": None,
            "starting_balance": 0,
            "statement_descriptor": None,
            "subscription": subscription.stripe_id,
            "subtotal": 1999,
            "tax": None,
            "tax_percent": None,
            "total": 1999,
            "webhooks_delivered_at": None
        }
        invoices.sync_invoice_from_stripe_data(data)
        self.assertTrue(SyncInvoiceItemsMock.called)
        self.assertEquals(Invoice.objects.filter(customer=self.customer).count(), 1)

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("pinax.stripe.actions.invoices.sync_invoice_items")
    @patch("pinax.stripe.actions.subscriptions.retrieve")
    def test_sync_invoice_from_stripe_data_no_subscription(self, RetrieveSubscriptionMock, SyncInvoiceItemsMock, SyncSubscriptionMock):
        SyncSubscriptionMock.return_value = None
        data = {
            "id": "in_17B6e8I10iPhvocMGtYd4hDD",
            "object": "invoice",
            "amount_due": 1999,
            "application_fee": None,
            "attempt_count": 0,
            "attempted": False,
            "charge": None,
            "closed": False,
            "currency": "usd",
            "customer": self.customer.stripe_id,
            "date": 1448470892,
            "description": None,
            "discount": None,
            "ending_balance": None,
            "forgiven": False,
            "lines": {
                "data": [{
                    "id": "ii_2342342",
                    "object": "line_item",
                    "amount": 2000,
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
                    "type": "line_item"
                }],
                "total_count": 1,
                "object": "list",
                "url": "/v1/invoices/in_17B6e8I10iPhvocMGtYd4hDD/lines"
            },
            "livemode": False,
            "metadata": {
            },
            "next_payment_attempt": 1448474492,
            "paid": False,
            "period_end": 1448470739,
            "period_start": 1448211539,
            "receipt_number": None,
            "starting_balance": 0,
            "statement_descriptor": None,
            "subscription": "",
            "subtotal": 2000,
            "tax": None,
            "tax_percent": None,
            "total": 2000,
            "webhooks_delivered_at": None
        }
        invoices.sync_invoice_from_stripe_data(data)
        self.assertTrue(SyncInvoiceItemsMock.called)
        self.assertEquals(Invoice.objects.filter(customer=self.customer).count(), 1)
        self.assertIsNone(Invoice.objects.filter(customer=self.customer)[0].subscription)

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("pinax.stripe.actions.invoices.sync_invoice_items")
    @patch("pinax.stripe.actions.subscriptions.retrieve")
    def test_sync_invoice_from_stripe_data_updated(self, RetrieveSubscriptionMock, SyncInvoiceItemsMock, SyncSubscriptionMock):
        plan = Plan.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        subscription = Subscription.objects.create(
            stripe_id="sub_7Q4BX0HMfqTpN8",
            customer=self.customer,
            plan=plan,
            quantity=1,
            status="active",
            start=timezone.now()
        )
        SyncSubscriptionMock.return_value = subscription
        data = {
            "id": "in_17B6e8I10iPhvocMGtYd4hDD",
            "object": "invoice",
            "amount_due": 1999,
            "application_fee": None,
            "attempt_count": 0,
            "attempted": False,
            "charge": None,
            "closed": False,
            "currency": "usd",
            "customer": self.customer.stripe_id,
            "date": 1448470892,
            "description": None,
            "discount": None,
            "ending_balance": None,
            "forgiven": False,
            "lines": {
                "data": [{
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
                }],
                "total_count": 1,
                "object": "list",
                "url": "/v1/invoices/in_17B6e8I10iPhvocMGtYd4hDD/lines"
            },
            "livemode": False,
            "metadata": {
            },
            "next_payment_attempt": 1448474492,
            "paid": False,
            "period_end": 1448470739,
            "period_start": 1448211539,
            "receipt_number": None,
            "starting_balance": 0,
            "statement_descriptor": None,
            "subscription": subscription.stripe_id,
            "subtotal": 1999,
            "tax": None,
            "tax_percent": None,
            "total": 1999,
            "webhooks_delivered_at": None
        }
        invoices.sync_invoice_from_stripe_data(data)
        self.assertTrue(SyncInvoiceItemsMock.called)
        self.assertEquals(Invoice.objects.filter(customer=self.customer).count(), 1)
        data.update({"paid": True})
        invoices.sync_invoice_from_stripe_data(data)
        self.assertEquals(Invoice.objects.filter(customer=self.customer).count(), 1)
        self.assertEquals(Invoice.objects.filter(customer=self.customer)[0].paid, True)


class TransfersTests(TestCase):

    def setUp(self):
        self.data = {
            "id": "tr_17BE31I10iPhvocMDwiBi4Pk",
            "object": "transfer",
            "amount": 1100,
            "amount_reversed": 0,
            "application_fee": None,
            "balance_transaction": "txn_179l3zI10iPhvocMhvKxAer7",
            "created": 1448499343,
            "currency": "usd",
            "date": 1448499343,
            "description": "Transfer to test@example.com",
            "destination": "ba_17BE31I10iPhvocMOUp6E9If",
            "failure_code": None,
            "failure_message": None,
            "livemode": False,
            "metadata": {
            },
            "recipient": "rp_17BE31I10iPhvocM14ZKPFfR",
            "reversals": {
                "object": "list",
                "data": [

                ],
                "has_more": False,
                "total_count": 0,
                "url": "/v1/transfers/tr_17BE31I10iPhvocMDwiBi4Pk/reversals"
            },
            "reversed": False,
            "source_transaction": None,
            "statement_descriptor": None,
            "status": "in_transit",
            "type": "bank_account"
        }
        self.event = Event.objects.create(
            stripe_id="evt_001",
            kind="transfer.paid",
            webhook_message={"data": {"object": self.data}},
            validated_message={"data": {"object": self.data}},
            valid=True,
            processed=False
        )

    def test_sync_transfer(self):
        transfers.sync_transfer(self.data, self.event)
        qs = Transfer.objects.filter(stripe_id=self.event.message["data"]["object"]["id"])
        self.assertEquals(qs.count(), 1)
        self.assertEquals(qs[0].event, self.event)

    def test_sync_transfer_update(self):
        transfers.sync_transfer(self.data, self.event)
        qs = Transfer.objects.filter(stripe_id=self.event.message["data"]["object"]["id"])
        self.assertEquals(qs.count(), 1)
        self.assertEquals(qs[0].event, self.event)
        self.event.validated_message["data"]["object"]["status"] = "paid"
        transfers.sync_transfer(self.event.message["data"]["object"], self.event)
        qs = Transfer.objects.filter(stripe_id=self.event.message["data"]["object"]["id"])
        self.assertEquals(qs[0].status, "paid")

    def test_transfer_during(self):
        Transfer.objects.create(
            stripe_id="tr_002",
            event=Event.objects.create(kind="transfer.created", webhook_message={}),
            amount=decimal.Decimal("100"),
            status="pending",
            date=timezone.now().replace(year=2015, month=1)
        )
        qs = transfers.during(2015, 1)
        self.assertEquals(qs.count(), 1)

    @patch("stripe.Transfer.retrieve")
    def test_transfer_update_status(self, RetrieveMock):
        RetrieveMock().status = "complete"
        transfer = Transfer.objects.create(
            stripe_id="tr_001",
            event=Event.objects.create(kind="transfer.created", webhook_message={}),
            amount=decimal.Decimal("100"),
            status="pending",
            date=timezone.now().replace(year=2015, month=1)
        )
        transfers.update_status(transfer)
        self.assertEquals(transfer.status, "complete")
