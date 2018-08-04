import datetime
import decimal
import json
import time
from unittest import skipIf

import django
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

import stripe
from mock import Mock, patch

from ..actions import (
    accounts,
    charges,
    customers,
    events,
    externalaccounts,
    invoices,
    plans,
    refunds,
    sources,
    subscriptions,
    transfers
)
from ..models import (
    Account,
    BitcoinReceiver,
    Card,
    Charge,
    Customer,
    Event,
    Invoice,
    Plan,
    Subscription,
    Transfer,
    UserAccount
)


class ChargesTests(TestCase):

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

    def test_create_no_customer_nor_source_raises_error(self):
        with self.assertRaises(ValueError) as exc:
            charges.create(amount=decimal.Decimal("10"),
                           customer=None)
            self.assertEquals(exc.exception.args, ("Must provide `customer` or `source`.",))

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
    def test_create_with_customer(self, CreateMock, SyncMock, SendReceiptMock):
        charges.create(amount=decimal.Decimal("10"), customer=self.customer)
        self.assertTrue(CreateMock.called)
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs, {
            "amount": 1000,
            "currency": "usd",
            "source": None,
            "customer": "cus_xxxxxxxxxxxxxxx",
            "stripe_account": None,
            "description": None,
            "capture": True,
            "idempotency_key": None,
        })
        self.assertTrue(SyncMock.called)
        self.assertTrue(SendReceiptMock.called)

    @patch("pinax.stripe.hooks.hookset.send_receipt")
    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Charge.create")
    def test_create_with_customer_id(self, CreateMock, SyncMock, SendReceiptMock):
        charges.create(amount=decimal.Decimal("10"), customer=self.customer.stripe_id)
        self.assertTrue(CreateMock.called)
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs, {
            "amount": 1000,
            "currency": "usd",
            "source": None,
            "customer": "cus_xxxxxxxxxxxxxxx",
            "stripe_account": None,
            "description": None,
            "capture": True,
            "idempotency_key": None,
        })
        self.assertTrue(SyncMock.called)
        self.assertTrue(SendReceiptMock.called)

    @patch("pinax.stripe.hooks.hookset.send_receipt")
    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Charge.create")
    def test_create_with_new_customer_id(self, CreateMock, SyncMock, SendReceiptMock):
        charges.create(amount=decimal.Decimal("10"), customer="cus_NEW")
        self.assertTrue(CreateMock.called)
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs, {
            "amount": 1000,
            "currency": "usd",
            "source": None,
            "customer": "cus_NEW",
            "stripe_account": None,
            "description": None,
            "capture": True,
            "idempotency_key": None,
        })
        self.assertTrue(SyncMock.called)
        self.assertTrue(SendReceiptMock.called)
        self.assertTrue(Customer.objects.get(stripe_id="cus_NEW"))

    @patch("pinax.stripe.hooks.hookset.send_receipt")
    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Charge.create")
    def test_create_with_idempotency_key(self, CreateMock, SyncMock, SendReceiptMock):
        charges.create(amount=decimal.Decimal("10"), customer=self.customer.stripe_id, idempotency_key="a")
        CreateMock.assert_called_once_with(
            amount=1000,
            capture=True,
            customer=self.customer.stripe_id,
            stripe_account=self.customer.stripe_account_stripe_id,
            idempotency_key="a",
            description=None,
            currency="usd",
            source=None,
        )

    @patch("pinax.stripe.hooks.hookset.send_receipt")
    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Charge.create")
    def test_create_with_app_fee(self, CreateMock, SyncMock, SendReceiptMock):
        charges.create(
            amount=decimal.Decimal("10"),
            customer=self.customer,
            destination_account="xxx",
            application_fee=decimal.Decimal("25")
        )
        self.assertTrue(CreateMock.called)
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["application_fee"], 2500)
        self.assertEqual(kwargs["destination"]["account"], "xxx")
        self.assertEqual(kwargs["destination"].get("amount"), None)
        self.assertTrue(SyncMock.called)
        self.assertTrue(SendReceiptMock.called)

    @patch("pinax.stripe.hooks.hookset.send_receipt")
    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Charge.create")
    def test_create_with_destination(self, CreateMock, SyncMock, SendReceiptMock):
        charges.create(
            amount=decimal.Decimal("10"),
            customer=self.customer,
            destination_account="xxx",
            destination_amount=decimal.Decimal("45")
        )
        self.assertTrue(CreateMock.called)
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["destination"]["account"], "xxx")
        self.assertEqual(kwargs["destination"]["amount"], 4500)
        self.assertTrue(SyncMock.called)
        self.assertTrue(SendReceiptMock.called)

    @patch("pinax.stripe.hooks.hookset.send_receipt")
    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Charge.create")
    def test_create_with_on_behalf_of(self, CreateMock, SyncMock, SendReceiptMock):
        charges.create(
            amount=decimal.Decimal("10"),
            customer=self.customer,
            on_behalf_of="account",
        )
        self.assertTrue(CreateMock.called)
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["on_behalf_of"], "account")
        self.assertTrue(SyncMock.called)
        self.assertTrue(SendReceiptMock.called)

    @patch("pinax.stripe.hooks.hookset.send_receipt")
    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Charge.create")
    def test_create_with_destination_and_on_behalf_of(self, CreateMock, SyncMock, SendReceiptMock):
        with self.assertRaises(ValueError):
            charges.create(
                amount=decimal.Decimal("10"),
                customer=self.customer,
                destination_account="xxx",
                on_behalf_of="account",
            )

    @patch("stripe.Charge.create")
    def test_create_not_decimal_raises_exception(self, CreateMock):
        with self.assertRaises(ValueError):
            charges.create(
                amount=decimal.Decimal("100"),
                customer=self.customer,
                application_fee=10
            )

    @patch("stripe.Charge.create")
    def test_create_app_fee_no_dest_raises_exception(self, CreateMock):
        with self.assertRaises(ValueError):
            charges.create(
                amount=decimal.Decimal("100"),
                customer=self.customer,
                application_fee=decimal.Decimal("10")
            )

    @patch("stripe.Charge.create")
    def test_create_app_fee_dest_acct_and_dest_amt_raises_exception(self, CreateMock):
        with self.assertRaises(ValueError):
            charges.create(
                amount=decimal.Decimal("100"),
                customer=self.customer,
                application_fee=decimal.Decimal("10"),
                destination_account="xxx",
                destination_amount=decimal.Decimal("15")
            )

    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Charge.capture")
    def test_capture(self, CaptureMock, SyncMock):
        charges.capture(Charge(stripe_id="ch_A", amount=decimal.Decimal("100"), currency="usd"))
        self.assertTrue(CaptureMock.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Charge.capture")
    def test_capture_with_amount(self, CaptureMock, SyncMock):
        charge = Charge(stripe_id="ch_A", amount=decimal.Decimal("100"), currency="usd")
        charges.capture(charge, amount=decimal.Decimal("50"), idempotency_key="IDEM")
        self.assertTrue(CaptureMock.called)
        _, kwargs = CaptureMock.call_args
        self.assertEquals(kwargs["amount"], 5000)
        self.assertEquals(kwargs["idempotency_key"], "IDEM")
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("stripe.Charge.capture")
    def test_capture_with_connect(self, CaptureMock, SyncMock):
        account = Account(stripe_id="acc_001")
        customer = Customer(stripe_id="cus_001", stripe_account=account)
        charges.capture(Charge(stripe_id="ch_A", amount=decimal.Decimal("100"), currency="usd", customer=customer))
        self.assertTrue(CaptureMock.called)
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.charges.sync_charge")
    def test_update_availability(self, SyncMock):
        Charge.objects.create(customer=self.customer, amount=decimal.Decimal("100"), currency="usd", paid=True, captured=True, available=False, refunded=False)
        charges.update_charge_availability()
        self.assertTrue(SyncMock.called)


class CustomersTests(TestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="patrick",
            email="paltman@example.com"
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
        original = Customer.objects.create(user=self.user, stripe_id="cus_XXXXX")

        new_customer = Mock()
        RetrieveMock.return_value = new_customer
        customer = customers.create(self.user)

        # But only one customer will exist - the original one
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(customer.stripe_id, original.stripe_id)

        # Check that the customer hasn't been modified
        self.assertEqual(customer.user, self.user)
        self.assertEqual(customer.stripe_id, "cus_XXXXX")
        CreateMock.assert_not_called()

    @patch("stripe.Customer.retrieve")
    @patch("stripe.Customer.create")
    def test_customer_create_local_customer_but_no_remote(self, CreateMock, RetrieveMock):
        # Create an existing database customer for this user
        Customer.objects.create(user=self.user, stripe_id="cus_XXXXX")

        RetrieveMock.side_effect = stripe.error.InvalidRequestError(
            message="invalid", param=None)

        # customers.Create will return a new customer instance
        CreateMock.return_value = {
            "id": "cus_YYYYY",
            "account_balance": 0,
            "currency": "us",
            "delinquent": False,
            "default_source": "",
            "sources": {"data": []},
            "subscriptions": {"data": []},
        }
        customer = customers.create(self.user)

        # But a customer *was* retrieved, but not found
        RetrieveMock.assert_called_once_with("cus_XXXXX")

        # But only one customer will exist - the original one
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(customer.stripe_id, "cus_YYYYY")

        # Check that the customer hasn't been modified
        self.assertEqual(customer.user, self.user)
        self.assertEqual(customer.stripe_id, "cus_YYYYY")
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["email"], self.user.email)
        self.assertIsNone(kwargs["source"])
        self.assertIsNone(kwargs["plan"])
        self.assertIsNone(kwargs["trial_end"])

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

    @patch("pinax.stripe.actions.invoices.create_and_pay")
    @patch("pinax.stripe.actions.customers.sync_customer")
    @patch("stripe.Customer.create")
    def test_customer_create_user_with_plan_and_quantity(self, CreateMock, SyncMock, CreateAndPayMock):
        Plan.objects.create(
            stripe_id="pro-monthly",
            name="Pro ($19.99/month each)",
            amount=19.99,
            interval="monthly",
            interval_count=1,
            currency="usd"
        )
        CreateMock.return_value = dict(id="cus_YYYYYYYYYYYYY")
        customer = customers.create(self.user, card="token232323", plan=self.plan, quantity=42)
        self.assertEqual(customer.user, self.user)
        self.assertEqual(customer.stripe_id, "cus_YYYYYYYYYYYYY")
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["email"], self.user.email)
        self.assertEqual(kwargs["source"], "token232323")
        self.assertEqual(kwargs["plan"], self.plan)
        self.assertEqual(kwargs["quantity"], 42)
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
    def test_purge_connected(self, RetrieveMock):
        account = Account.objects.create(stripe_id="acc_XXX")
        customer = Customer.objects.create(
            user=self.user,
            stripe_account=account,
            stripe_id="cus_xxxxxxxxxxxxxxx",
        )
        UserAccount.objects.create(user=self.user, account=account, customer=customer)
        customers.purge(customer)
        self.assertTrue(RetrieveMock().delete.called)
        self.assertIsNone(Customer.objects.get(stripe_id=customer.stripe_id).user)
        self.assertIsNotNone(Customer.objects.get(stripe_id=customer.stripe_id).date_purged)
        self.assertFalse(UserAccount.objects.exists())
        self.assertTrue(self.User.objects.exists())

    @patch("stripe.Customer.retrieve")
    def test_purge_already_deleted(self, RetrieveMock):
        RetrieveMock().delete.side_effect = stripe.error.InvalidRequestError("No such customer:", "error")
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
        RetrieveMock().delete.side_effect = stripe.error.InvalidRequestError("Bad", "error")
        customer = Customer.objects.create(
            user=self.user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        with self.assertRaises(stripe.error.InvalidRequestError):
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

    @patch("pinax.stripe.actions.customers.sync_customer")
    def test_link_customer(self, SyncMock):
        Customer.objects.create(stripe_id="cu_123")
        message = dict(data=dict(object=dict(id="cu_123")))
        event = Event.objects.create(validated_message=message, kind="customer.created")
        customers.link_customer(event)
        self.assertEquals(event.customer.stripe_id, "cu_123")
        self.assertTrue(SyncMock.called)

    def test_link_customer_non_customer_event(self):
        Customer.objects.create(stripe_id="cu_123")
        message = dict(data=dict(object=dict(customer="cu_123")))
        event = Event.objects.create(validated_message=message, kind="invoice.created")
        customers.link_customer(event)
        self.assertEquals(event.customer.stripe_id, "cu_123")

    def test_link_customer_non_customer_event_no_customer(self):
        Customer.objects.create(stripe_id="cu_123")
        message = dict(data=dict(object=dict()))
        event = Event.objects.create(validated_message=message, kind="transfer.created")
        customers.link_customer(event)
        self.assertIsNone(event.customer, "cu_123")

    @patch("pinax.stripe.actions.customers.sync_customer")
    def test_link_customer_does_not_exist(self, SyncMock):
        message = dict(data=dict(object=dict(id="cu_123")))
        event = Event.objects.create(stripe_id="evt_1", validated_message=message, kind="customer.created")
        customers.link_customer(event)
        Customer.objects.get(stripe_id="cu_123")
        self.assertTrue(SyncMock.called)

    @patch("pinax.stripe.actions.customers.sync_customer")
    def test_link_customer_does_not_exist_connected(self, SyncMock):
        message = dict(data=dict(object=dict(id="cu_123")))
        account = Account.objects.create(stripe_id="acc_XXX")
        event = Event.objects.create(stripe_id="evt_1", validated_message=message, kind="customer.created", stripe_account=account)
        customers.link_customer(event)
        Customer.objects.get(stripe_id="cu_123", stripe_account=account)
        self.assertTrue(SyncMock.called)


class CustomersWithConnectTests(TestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="patrick",
            email="paltman@example.com"
        )
        self.plan = Plan.objects.create(
            stripe_id="p1",
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )
        self.account = Account.objects.create(
            stripe_id="acc_XXX"
        )

    def test_get_customer_for_user_with_stripe_account(self):
        expected = Customer.objects.create(
            stripe_id="x",
            stripe_account=self.account)
        UserAccount.objects.create(user=self.user, account=self.account, customer=expected)
        actual = customers.get_customer_for_user(
            self.user, stripe_account=self.account)
        self.assertEquals(expected, actual)

    def test_get_customer_for_user_with_stripe_account_and_legacy_customer(self):
        Customer.objects.create(user=self.user, stripe_id="x")
        self.assertIsNone(customers.get_customer_for_user(
            self.user, stripe_account=self.account))

    @patch("pinax.stripe.actions.customers.sync_customer")
    @patch("stripe.Customer.create")
    def test_customer_create_with_connect(self, CreateMock, SyncMock):
        CreateMock.return_value = dict(id="cus_XXXXX")
        customer = customers.create(self.user, stripe_account=self.account)
        self.assertIsNone(customer.user)
        self.assertEqual(customer.stripe_id, "cus_XXXXX")
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["email"], self.user.email)
        self.assertEqual(kwargs["stripe_account"], self.account.stripe_id)
        self.assertIsNone(kwargs["source"])
        self.assertIsNone(kwargs["plan"])
        self.assertIsNone(kwargs["trial_end"])
        self.assertTrue(SyncMock.called)

    @patch("stripe.Customer.retrieve")
    @patch("pinax.stripe.actions.customers.sync_customer")
    @patch("stripe.Customer.create")
    def test_customer_create_with_connect_and_stale_user_account(self, CreateMock, SyncMock, RetrieveMock):
        CreateMock.return_value = dict(id="cus_XXXXX")
        RetrieveMock.side_effect = stripe.error.InvalidRequestError(
            message="Not Found", param="stripe_id"
        )
        ua = UserAccount.objects.create(
            user=self.user,
            account=self.account,
            customer=Customer.objects.create(stripe_id="cus_Z", stripe_account=self.account))
        customer = customers.create(self.user, stripe_account=self.account)
        self.assertIsNone(customer.user)
        self.assertEqual(customer.stripe_id, "cus_XXXXX")
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["email"], self.user.email)
        self.assertEqual(kwargs["stripe_account"], self.account.stripe_id)
        self.assertIsNone(kwargs["source"])
        self.assertIsNone(kwargs["plan"])
        self.assertIsNone(kwargs["trial_end"])
        self.assertTrue(SyncMock.called)
        self.assertEqual(self.user.user_accounts.get(), ua)
        self.assertEqual(ua.customer, customer)
        RetrieveMock.assert_called_once_with("cus_Z", stripe_account=self.account.stripe_id)

    @patch("stripe.Customer.retrieve")
    def test_customer_create_with_connect_with_existing_customer(self, RetrieveMock):
        expected = Customer.objects.create(
            stripe_id="x",
            stripe_account=self.account)
        UserAccount.objects.create(user=self.user, account=self.account, customer=expected)
        customer = customers.create(self.user, stripe_account=self.account)
        self.assertEquals(customer, expected)
        RetrieveMock.assert_called_once_with("x", stripe_account=self.account.stripe_id)

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
        customer = customers.create(self.user, card="token232323", plan=self.plan, stripe_account=self.account)
        self.assertEqual(customer.stripe_id, "cus_YYYYYYYYYYYYY")
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["email"], self.user.email)
        self.assertEqual(kwargs["source"], "token232323")
        self.assertEqual(kwargs["plan"], self.plan)
        self.assertIsNotNone(kwargs["trial_end"])
        self.assertTrue(SyncMock.called)
        self.assertTrue(CreateAndPayMock.called)


class EventsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super(EventsTests, cls).setUpClass()
        cls.account = Account.objects.create(stripe_id="acc_001")

    def test_dupe_event_exists(self):
        Event.objects.create(stripe_id="evt_003", kind="foo", livemode=True, webhook_message="{}", api_version="", request="", pending_webhooks=0)
        self.assertTrue(events.dupe_event_exists("evt_003"))

    @patch("pinax.stripe.webhooks.AccountUpdatedWebhook.process")
    def test_add_event(self, ProcessMock):
        events.add_event(stripe_id="evt_001", kind="account.updated", livemode=True, message={})
        event = Event.objects.get(stripe_id="evt_001")
        self.assertEquals(event.kind, "account.updated")
        self.assertTrue(ProcessMock.called)

    @patch("pinax.stripe.webhooks.AccountUpdatedWebhook.process")
    def test_add_event_connect(self, ProcessMock):
        events.add_event(stripe_id="evt_001", kind="account.updated", livemode=True, message={"account": self.account.stripe_id})
        event = Event.objects.get(stripe_id="evt_001", stripe_account=self.account)
        self.assertEquals(event.kind, "account.updated")
        self.assertTrue(ProcessMock.called)

    @patch("pinax.stripe.webhooks.AccountUpdatedWebhook.process")
    def test_add_event_missing_account_connect(self, ProcessMock):
        events.add_event(stripe_id="evt_001", kind="account.updated", livemode=True, message={"account": "acc_NEW"})
        event = Event.objects.get(stripe_id="evt_001", stripe_account=Account.objects.get(stripe_id="acc_NEW"))
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
        invoice.pay.side_effect = stripe.error.InvalidRequestError("Bad", "error")
        self.assertFalse(invoices.create_and_pay(Mock()))
        self.assertTrue(invoice.pay.called)

    @patch("stripe.Invoice.create")
    def test_create_and_pay_invalid_request_error_on_create(self, CreateMock):
        CreateMock.side_effect = stripe.error.InvalidRequestError("Bad", "error")
        self.assertFalse(invoices.create_and_pay(Mock()))


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
        self.assertEqual(result, (0, {"pinax_stripe.Card": 0}))
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
            email="paltman@example.com"
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
            email="paltman@example.com"
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

    @classmethod
    def setUpClass(cls):
        super(SubscriptionsTests, cls).setUpClass()
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            username="patrick",
            email="paltman@example.com"
        )
        cls.customer = Customer.objects.create(
            user=cls.user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        cls.plan = Plan.objects.create(
            stripe_id="the-plan",
            amount=2,
            interval_count=1,
        )
        cls.account = Account.objects.create(stripe_id="acct_xx")
        cls.connected_customer = Customer.objects.create(
            stripe_id="cus_yyyyyyyyyyyyyyy",
            stripe_account=cls.account,
        )
        UserAccount.objects.create(user=cls.user,
                                   customer=cls.connected_customer,
                                   account=cls.account)

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

    @patch("stripe.Subscription")
    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_cancel_subscription(self, SyncMock, StripeSubMock):
        subscription = Subscription(stripe_id="sub_X", customer=self.customer)
        obj = object()
        SyncMock.return_value = obj
        sub = subscriptions.cancel(subscription)
        self.assertIs(sub, obj)
        self.assertTrue(SyncMock.called)
        _, kwargs = StripeSubMock.call_args
        self.assertEquals(kwargs["stripe_account"], None)

    @patch("stripe.Subscription")
    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_cancel_subscription_with_account(self, SyncMock, StripeSubMock):
        subscription = Subscription(stripe_id="sub_X", customer=self.connected_customer)
        subscriptions.cancel(subscription)
        _, kwargs = StripeSubMock.call_args
        self.assertEquals(kwargs["stripe_account"], self.account.stripe_id)

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    def test_update(self, SyncMock):
        SubMock = Mock()
        SubMock.customer = self.customer
        obj = object()
        SyncMock.return_value = obj
        sub = subscriptions.update(SubMock)
        self.assertIs(sub, obj)
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
        self.assertEquals(SubMock.stripe_subscription.trial_end, "now")
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

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("stripe.Subscription.create")
    def test_subscription_create(self, SubscriptionCreateMock, SyncMock):
        subscriptions.create(self.customer, "the-plan")
        self.assertTrue(SyncMock.called)
        self.assertTrue(SubscriptionCreateMock.called)

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("stripe.Subscription.create")
    def test_subscription_create_with_trial(self, SubscriptionCreateMock, SyncMock):
        subscriptions.create(self.customer, "the-plan", trial_days=3)
        self.assertTrue(SubscriptionCreateMock.called)
        _, kwargs = SubscriptionCreateMock.call_args
        self.assertEquals(kwargs["trial_end"].date(), (datetime.datetime.utcnow() + datetime.timedelta(days=3)).date())

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("stripe.Subscription.create")
    def test_subscription_create_token(self, SubscriptionCreateMock, CustomerMock):
        subscriptions.create(self.customer, "the-plan", token="token")
        self.assertTrue(SubscriptionCreateMock.called)
        _, kwargs = SubscriptionCreateMock.call_args
        self.assertEquals(kwargs["source"], "token")

    @patch("stripe.Subscription.create")
    def test_subscription_create_with_connect(self, SubscriptionCreateMock):
        SubscriptionCreateMock.return_value = {
            "object": "subscription",
            "id": "sub_XX",
            "application_fee_percent": None,
            "cancel_at_period_end": False,
            "canceled_at": None,
            "current_period_start": 1509978774,
            "current_period_end": 1512570774,
            "ended_at": None,
            "quantity": 1,
            "start": 1509978774,
            "status": "active",
            "trial_start": None,
            "trial_end": None,
            "plan": {
                "id": self.plan.stripe_id,
            }}
        subscriptions.create(self.connected_customer, self.plan.stripe_id)
        SubscriptionCreateMock.assert_called_once_with(
            coupon=None,
            customer=self.connected_customer.stripe_id,
            plan="the-plan",
            quantity=4,
            stripe_account="acct_xx",
            tax_percent=None)
        subscription = Subscription.objects.get()
        self.assertEqual(subscription.customer, self.connected_customer)

    @patch("stripe.Subscription.retrieve")
    @patch("stripe.Subscription.create")
    def test_retrieve_subscription_with_connect(self, CreateMock, RetrieveMock):
        CreateMock.return_value = {
            "object": "subscription",
            "id": "sub_XX",
            "application_fee_percent": None,
            "cancel_at_period_end": False,
            "canceled_at": None,
            "current_period_start": 1509978774,
            "current_period_end": 1512570774,
            "ended_at": None,
            "quantity": 1,
            "start": 1509978774,
            "status": "active",
            "trial_start": None,
            "trial_end": None,
            "plan": {
                "id": self.plan.stripe_id,
            }}
        subscriptions.create(self.connected_customer, self.plan.stripe_id)
        subscriptions.retrieve(self.connected_customer, "sub_XX")
        RetrieveMock.assert_called_once_with("sub_XX", stripe_account=self.account.stripe_id)

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
            email="paltman@example.com"
        )
        self.customer = Customer.objects.create(
            user=self.user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )

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

    def test_sync_plan(self):
        """
        Test that a single Plan is updated
        """
        Plan.objects.create(
            stripe_id="pro2",
            name="Plan Plan",
            interval="month",
            interval_count=1,
            amount=decimal.Decimal("19.99")
        )
        plan = {
            "id": "pro2",
            "object": "plan",
            "amount": 1999,
            "created": 1448121054,
            "currency": "usd",
            "interval": "month",
            "interval_count": 1,
            "livemode": False,
            "metadata": {},
            "name": "Gold Plan",
            "statement_descriptor": "ALTMAN",
            "trial_period_days": 3
        }
        plans.sync_plan(plan)
        self.assertTrue(Plan.objects.all().count(), 1)
        self.assertEquals(Plan.objects.get(stripe_id="pro2").name, plan["name"])

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

    def test_sync_payment_source_from_stripe_data_source_card(self):
        source = {
            "id": "src_123",
            "object": "source",
            "amount": None,
            "client_secret": "src_client_secret_123",
            "created": 1483575790,
            "currency": None,
            "flow": "none",
            "livemode": False,
            "metadata": {},
            "owner": {
                "address": None,
                "email": None,
                "name": None,
                "phone": None,
                "verified_address": None,
                "verified_email": None,
                "verified_name": None,
                "verified_phone": None,
            },
            "status": "chargeable",
            "type": "card",
            "usage": "reusable",
            "card": {
                "brand": "Visa",
                "country": "US",
                "exp_month": 12,
                "exp_year": 2034,
                "funding": "debit",
                "last4": "5556",
                "three_d_secure": "not_supported"
            }
        }
        sources.sync_payment_source_from_stripe_data(self.customer, source)
        self.assertFalse(Card.objects.exists())

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
        sub = subscriptions.sync_subscription_from_stripe_data(self.customer, subscription)
        self.assertEquals(Subscription.objects.get(stripe_id=subscription["id"]), sub)
        self.assertEquals(sub.status, "trialing")

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

    @patch("pinax.stripe.actions.customers.purge_local")
    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("pinax.stripe.actions.sources.sync_payment_source_from_stripe_data")
    @patch("stripe.Customer.retrieve")
    def test_sync_customer_purged_locally(self, RetrieveMock, SyncPaymentSourceMock, SyncSubscriptionMock, PurgeLocalMock):
        self.customer.date_purged = timezone.now()
        customers.sync_customer(self.customer)
        self.assertFalse(RetrieveMock.called)
        self.assertFalse(SyncPaymentSourceMock.called)
        self.assertFalse(SyncSubscriptionMock.called)
        self.assertFalse(PurgeLocalMock.called)

    @patch("pinax.stripe.actions.customers.purge_local")
    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("pinax.stripe.actions.sources.sync_payment_source_from_stripe_data")
    @patch("stripe.Customer.retrieve")
    def test_sync_customer_purged_remotely_not_locally(self, RetrieveMock, SyncPaymentSourceMock, SyncSubscriptionMock, PurgeLocalMock):
        RetrieveMock.return_value = dict(
            deleted=True
        )
        customers.sync_customer(self.customer)
        self.assertFalse(SyncPaymentSourceMock.called)
        self.assertFalse(SyncSubscriptionMock.called)
        self.assertTrue(PurgeLocalMock.called)

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

    def test_sync_charge_from_stripe_data_balance_transaction(self):
        data = {
            "id": "ch_17A1dUI10iPhvocMOecpvQlI",
            "object": "charge",
            "amount": 200,
            "amount_refunded": 0,
            "application_fee": None,
            "balance_transaction": {
                "id": "txn_19XJJ02eZvKYlo2ClwuJ1rbA",
                "object": "balance_transaction",
                "amount": 999,
                "available_on": 1483920000,
                "created": 1483315442,
                "currency": "usd",
                "description": None,
                "fee": 59,
                "fee_details": [
                    {
                        "amount": 59,
                        "application": None,
                        "currency": "usd",
                        "description": "Stripe processing fees",
                        "type": "stripe_fee"
                    }
                ],
                "net": 940,
                "source": "ch_19XJJ02eZvKYlo2CHfSUsSpl",
                "status": "pending",
                "type": "charge"
            },
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
        self.assertEquals(charge.available, False)
        self.assertEquals(charge.fee, decimal.Decimal("0.59"))
        self.assertEquals(charge.currency, "usd")

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
        self.assertEqual(charge.outcome["risk_level"], "normal")

    @patch("stripe.Subscription.retrieve")
    def test_retrieve_stripe_subscription(self, RetrieveMock):
        RetrieveMock.return_value = stripe.Subscription(
            customer="cus_xxxxxxxxxxxxxxx"
        )
        value = subscriptions.retrieve(self.customer, "sub id")
        self.assertEquals(value, RetrieveMock.return_value)

    def test_retrieve_stripe_subscription_no_sub_id(self):
        value = subscriptions.retrieve(self.customer, None)
        self.assertIsNone(value)

    @patch("stripe.Subscription.retrieve")
    def test_retrieve_stripe_subscription_diff_customer(self, RetrieveMock):
        class Subscription:
            customer = "cus_xxxxxxxxxxxxZZZ"

        RetrieveMock.return_value = Subscription()

        value = subscriptions.retrieve(self.customer, "sub_id")
        self.assertIsNone(value)

    @patch("stripe.Subscription.retrieve")
    def test_retrieve_stripe_subscription_missing_subscription(self, RetrieveMock):
        RetrieveMock.return_value = None
        value = subscriptions.retrieve(self.customer, "sub id")
        self.assertIsNone(value)

    @patch("stripe.Subscription.retrieve")
    def test_retrieve_stripe_subscription_invalid_request(self, RetrieveMock):
        def bad_request(*args, **kwargs):
            raise stripe.error.InvalidRequestError("Bad", "error")
        RetrieveMock.side_effect = bad_request
        with self.assertRaises(stripe.error.InvalidRequestError):
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
        self.assertEquals(invoice.items.count(), 2)

        items[1].update({"description": "This is your second subscription"})
        invoices.sync_invoice_items(invoice, items)
        self.assertEquals(invoice.items.count(), 2)
        self.assertEquals(invoice.items.get(stripe_id="sub_7Q4BX0HMfqTpN9").description, "This is your second subscription")


class InvoiceSyncsTests(TestCase):

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

        plan = Plan.objects.create(stripe_id="pro2", interval="month", interval_count=1, amount=decimal.Decimal("19.99"))
        self.subscription = Subscription.objects.create(
            stripe_id="sub_7Q4BX0HMfqTpN8",
            customer=self.customer,
            plan=plan,
            quantity=1,
            status="active",
            start=timezone.now()
        )
        self.invoice_data = {
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
                    "id": self.subscription.stripe_id,
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
            "subscription": self.subscription.stripe_id,
            "subtotal": 1999,
            "tax": None,
            "tax_percent": None,
            "total": 1999,
            "webhooks_delivered_at": None
        }
        self.account = Account.objects.create(stripe_id="acct_X")

    @patch("pinax.stripe.hooks.hookset.send_receipt")
    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("stripe.Charge.retrieve")
    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("pinax.stripe.actions.invoices.sync_invoice_items")
    @patch("pinax.stripe.actions.subscriptions.retrieve")
    def test_sync_invoice_from_stripe_data(self, RetrieveSubscriptionMock, SyncInvoiceItemsMock, SyncChargeMock, ChargeFetchMock, SyncSubscriptionMock, SendReceiptMock):
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
        self.invoice_data["charge"] = charge.stripe_id
        SyncChargeMock.return_value = charge
        SyncSubscriptionMock.return_value = self.subscription
        invoices.sync_invoice_from_stripe_data(self.invoice_data)
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
        self.invoice_data["charge"] = charge.stripe_id
        SyncChargeMock.return_value = charge
        SyncSubscriptionMock.return_value = self.subscription
        invoices.sync_invoice_from_stripe_data(self.invoice_data, send_receipt=False)
        self.assertTrue(SyncInvoiceItemsMock.called)
        self.assertEquals(Invoice.objects.filter(customer=self.customer).count(), 1)
        self.assertTrue(ChargeFetchMock.called)
        self.assertTrue(SyncChargeMock.called)
        self.assertFalse(SendReceiptMock.called)

    @patch("pinax.stripe.hooks.hookset.send_receipt")
    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("stripe.Charge.retrieve")
    @patch("pinax.stripe.actions.charges.sync_charge_from_stripe_data")
    @patch("pinax.stripe.actions.invoices.sync_invoice_items")
    @patch("pinax.stripe.actions.subscriptions.retrieve")
    def test_sync_invoice_from_stripe_data_connect(self, RetrieveSubscriptionMock, SyncInvoiceItemsMock, SyncChargeMock, ChargeFetchMock, SyncSubscriptionMock, SendReceiptMock):
        self.invoice_data["charge"] = "ch_XXXXXX"
        self.customer.stripe_account = self.account
        self.customer.save()
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
        SyncSubscriptionMock.return_value = self.subscription
        invoices.sync_invoice_from_stripe_data(self.invoice_data)
        self.assertTrue(SyncInvoiceItemsMock.called)
        self.assertEquals(Invoice.objects.filter(customer=self.customer).count(), 1)
        self.assertTrue(ChargeFetchMock.called)
        args, kwargs = ChargeFetchMock.call_args
        self.assertEquals(args, ("ch_XXXXXX",))
        self.assertEquals(kwargs, {"stripe_account": "acct_X",
                                   "expand": ["balance_transaction"]})
        self.assertTrue(SyncChargeMock.called)
        self.assertTrue(SendReceiptMock.called)

    @patch("pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data")
    @patch("pinax.stripe.actions.invoices.sync_invoice_items")
    @patch("pinax.stripe.actions.subscriptions.retrieve")
    def test_sync_invoice_from_stripe_data_no_charge(self, RetrieveSubscriptionMock, SyncInvoiceItemsMock, SyncSubscriptionMock):
        SyncSubscriptionMock.return_value = self.subscription
        self.invoice_data["charge"] = None
        invoices.sync_invoice_from_stripe_data(self.invoice_data)
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
        SyncSubscriptionMock.return_value = self.subscription
        data = self.invoice_data
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

    @patch("stripe.Transfer.create")
    def test_transfer_create(self, CreateMock):
        CreateMock.return_value = self.data
        transfers.create(decimal.Decimal("100"), "usd", None, None)
        self.assertTrue(CreateMock.called)

    @patch("stripe.Transfer.create")
    def test_transfer_create_with_transfer_group(self, CreateMock):
        CreateMock.return_value = self.data
        transfers.create(decimal.Decimal("100"), "usd", None, None, transfer_group="foo")
        _, kwargs = CreateMock.call_args
        self.assertEquals(kwargs["transfer_group"], "foo")

    @patch("stripe.Transfer.create")
    def test_transfer_create_with_stripe_account(self, CreateMock):
        CreateMock.return_value = self.data
        transfers.create(decimal.Decimal("100"), "usd", None, None, stripe_account="foo")
        _, kwargs = CreateMock.call_args
        self.assertEquals(kwargs["stripe_account"], "foo")


class AccountsSyncTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super(AccountsSyncTestCase, cls).setUpClass()

        cls.custom_account_data = json.loads(
            """{
      "type":"custom",
      "tos_acceptance":{
        "date":1490903452,
        "ip":"123.107.1.28",
        "user_agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
      },
      "business_logo":null,
      "email":"operations@someurl.com",
      "timezone":"Etc/UTC",
      "statement_descriptor":"SOME COMP",
      "default_currency":"cad",
      "payout_schedule":{
        "delay_days":3,
        "interval":"manual"
      },
      "display_name":"Some Company",
      "payout_statement_descriptor": "For reals",
      "id":"acct_1A39IGDwqdd5icDO",
      "payouts_enabled":true,
      "external_accounts":{
        "has_more":false,
        "total_count":1,
        "object":"list",
        "data":[
          {
            "routing_number":"11000-000",
            "bank_name":"SOME CREDIT UNION",
            "account":"acct_1A39IGDwqdd5icDO",
            "object":"bank_account",
            "currency":"cad",
            "country":"CA",
            "account_holder_name":"Luke Burden",
            "last4":"6789",
            "status":"new",
            "fingerprint":"bZJnuqqS4qIX0SX0",
            "account_holder_type":"individual",
            "default_for_currency":true,
            "id":"ba_1A39IGDwqdd5icDOn9VrFXlQ",
            "metadata":{}
          }
        ],
        "url":"/v1/accounts/acct_1A39IGDwqdd5icDO/external_accounts"
      },
      "support_email":"support@someurl.com",
      "metadata":{
        "user_id":"9428"
      },
      "support_phone":"7788188181",
      "business_name":"Woop Woop",
      "object":"account",
      "charges_enabled":true,
      "business_name":"Woop Woop",
      "debit_negative_balances":false,
      "country":"CA",
      "decline_charge_on":{
        "avs_failure":true,
        "cvc_failure":true
      },
      "product_description":"Monkey Magic",
      "legal_entity":{
        "personal_id_number_provided":false,
        "first_name":"Luke",
        "last_name":"Baaard",
        "dob":{
          "month":2,
          "day":3,
          "year":1999
        },
        "personal_address":{
          "city":null,
          "country":"CA",
          "line2":null,
          "line1":null,
          "state":null,
          "postal_code":null
        },
        "business_tax_id_provided":false,
        "verification":{
          "status":"unverified",
          "details_code":"failed_keyed_identity",
          "document":null,
          "details":"Provided identity information could not be verified"
        },
        "address":{
          "city":"Vancouver",
          "country":"CA",
          "line2":null,
          "line1":"14 Alberta St",
          "state":"BC",
          "postal_code":"V5Y4Z2"
        },
        "business_name":null,
        "type":"individual"
      },
      "details_submitted":true,
      "verification":{
        "due_by":null,
        "fields_needed":[
          "legal_entity.personal_id_number"
        ],
        "disabled_reason":null
      }
    }""")
        cls.custom_account_data_no_dob_no_verification_no_tosacceptance = json.loads(
            """{
      "type":"custom",
      "tos_acceptance":{
        "date":null,
        "ip":"123.107.1.28",
        "user_agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
      },
      "business_logo":null,
      "email":"operations@someurl.com",
      "timezone":"Etc/UTC",
      "statement_descriptor":"SOME COMP",
      "default_currency":"cad",
      "payout_schedule":{
        "delay_days":3,
        "interval":"manual"
      },
      "display_name":"Some Company",
      "payout_statement_descriptor": "For reals",
      "id":"acct_1A39IGDwqdd5icDO",
      "payouts_enabled":true,
      "external_accounts":{
        "has_more":false,
        "total_count":1,
        "object":"list",
        "data":[
          {
            "routing_number":"11000-000",
            "bank_name":"SOME CREDIT UNION",
            "account":"acct_1A39IGDwqdd5icDO",
            "object":"other",
            "currency":"cad",
            "country":"CA",
            "account_holder_name":"Luke Burden",
            "last4":"6789",
            "status":"new",
            "fingerprint":"bZJnuqqS4qIX0SX0",
            "account_holder_type":"individual",
            "default_for_currency":true,
            "id":"ba_1A39IGDwqdd5icDOn9VrFXlQ",
            "metadata":{}
          }
        ],
        "url":"/v1/accounts/acct_1A39IGDwqdd5icDO/external_accounts"
      },
      "support_email":"support@someurl.com",
      "metadata":{
        "user_id":"9428"
      },
      "support_phone":"7788188181",
      "business_name":"Woop Woop",
      "object":"account",
      "charges_enabled":true,
      "business_name":"Woop Woop",
      "debit_negative_balances":false,
      "country":"CA",
      "decline_charge_on":{
        "avs_failure":true,
        "cvc_failure":true
      },
      "product_description":"Monkey Magic",
      "legal_entity":{
        "dob": null,
        "verification": null,
        "personal_id_number_provided":false,
        "first_name":"Luke",
        "last_name":"Baaard",
        "personal_address":{
          "city":null,
          "country":"CA",
          "line2":null,
          "line1":null,
          "state":null,
          "postal_code":null
        },
        "business_tax_id_provided":false,
        "address":{
          "city":"Vancouver",
          "country":"CA",
          "line2":null,
          "line1":"14 Alberta St",
          "state":"BC",
          "postal_code":"V5Y4Z2"
        },
        "business_name":null,
        "type":"individual"
      },
      "details_submitted":true,
      "verification":{
        "due_by":null,
        "fields_needed":[
          "legal_entity.personal_id_number"
        ],
        "disabled_reason":null
      }
    }""")
        cls.not_custom_account_data = json.loads(
            """{
      "business_logo":null,
      "business_name":"Woop Woop",
      "business_url":"https://www.someurl.com",
      "charges_enabled":true,
      "country":"CA",
      "default_currency":"cad",
      "details_submitted":true,
      "display_name":"Some Company",
      "email":"operations@someurl.com",
      "id":"acct_102t2K2m3chDH8uL",
      "object":"account",
      "payouts_enabled": true,
      "statement_descriptor":"SOME COMP",
      "support_address": {
        "city": null,
        "country": "DE",
        "line1": null,
        "line2": null,
        "postal_code": null,
        "state": null
      },
      "support_email":"support@someurl.com",
      "support_phone":"7788188181",
      "support_url":"https://support.someurl.com",
      "timezone":"Etc/UTC",
      "type":"standard"
    }""")

    def assert_common_attributes(self, account):
        self.assertEqual(account.support_phone, "7788188181")
        self.assertEqual(account.business_name, "Woop Woop")
        self.assertEqual(account.country, "CA")
        self.assertEqual(account.charges_enabled, True)
        self.assertEqual(account.support_email, "support@someurl.com")
        self.assertEqual(account.details_submitted, True)
        self.assertEqual(account.email, "operations@someurl.com")
        self.assertEqual(account.timezone, "Etc/UTC")
        self.assertEqual(account.display_name, "Some Company")
        self.assertEqual(account.statement_descriptor, "SOME COMP")
        self.assertEqual(account.default_currency, "cad")

    def assert_custom_attributes(self, account, dob=None, verification=None, acceptance_date=None, bank_accounts=0):

        # extra top level attributes
        self.assertEqual(account.debit_negative_balances, False)
        self.assertEqual(account.product_description, "Monkey Magic")
        self.assertEqual(account.metadata, {"user_id": "9428"})
        self.assertEqual(account.payout_statement_descriptor, "For reals")

        # legal entity
        self.assertEqual(account.legal_entity_address_city, "Vancouver")
        self.assertEqual(account.legal_entity_address_country, "CA")
        self.assertEqual(account.legal_entity_address_line1, "14 Alberta St")
        self.assertEqual(account.legal_entity_address_line2, None)
        self.assertEqual(account.legal_entity_address_postal_code, "V5Y4Z2")
        self.assertEqual(account.legal_entity_address_state, "BC")
        self.assertEqual(account.legal_entity_dob, dob)
        self.assertEqual(account.legal_entity_type, "individual")
        self.assertEqual(account.legal_entity_first_name, "Luke")
        self.assertEqual(account.legal_entity_last_name, "Baaard")
        self.assertEqual(account.legal_entity_personal_id_number_provided, False)

        # verification
        if verification is not None:
            self.assertEqual(
                account.legal_entity_verification_details,
                "Provided identity information could not be verified"
            )
            self.assertEqual(
                account.legal_entity_verification_details_code, "failed_keyed_identity"
            )
            self.assertEqual(account.legal_entity_verification_document, None)
            self.assertEqual(account.legal_entity_verification_status, "unverified")

        self.assertEqual(
            account.tos_acceptance_date,
            acceptance_date
        )

        self.assertEqual(account.tos_acceptance_ip, "123.107.1.28")
        self.assertEqual(
            account.tos_acceptance_user_agent,
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
        )

        # decline charge on certain conditions
        self.assertEqual(account.decline_charge_on_avs_failure, True)
        self.assertEqual(account.decline_charge_on_cvc_failure, True)

        # Payout schedule
        self.assertEqual(account.payout_schedule_interval, "manual")
        self.assertEqual(account.payout_schedule_delay_days, 3)
        self.assertEqual(account.payout_schedule_weekly_anchor, None)
        self.assertEqual(account.payout_schedule_monthly_anchor, None)

        # verification status, key to progressing account setup
        self.assertEqual(account.verification_disabled_reason, None)
        self.assertEqual(account.verification_due_by, None)
        self.assertEqual(
            account.verification_fields_needed,
            [
                "legal_entity.personal_id_number"
            ]
        )

        # external accounts should be sync'd - leave the detail check to
        # its own test
        self.assertEqual(
            account.bank_accounts.all().count(), bank_accounts
        )

    def test_sync_custom_account(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="snuffle",
            email="upagus@test"
        )
        account = accounts.sync_account_from_stripe_data(
            self.custom_account_data, user=user
        )
        self.assertEqual(account.type, "custom")
        self.assert_common_attributes(account)
        self.assert_custom_attributes(
            account,
            dob=datetime.date(1999, 2, 3),
            verification="full",
            acceptance_date=datetime.datetime(2017, 3, 30, 19, 50, 52),
            bank_accounts=1
        )

    @patch("pinax.stripe.actions.externalaccounts.sync_bank_account_from_stripe_data")
    def test_sync_custom_account_no_dob_no_verification(self, SyncMock):
        User = get_user_model()
        user = User.objects.create_user(
            username="snuffle",
            email="upagus@test"
        )
        account = accounts.sync_account_from_stripe_data(
            self.custom_account_data_no_dob_no_verification_no_tosacceptance, user=user
        )
        self.assertEqual(account.type, "custom")
        self.assert_common_attributes(account)
        self.assert_custom_attributes(account)
        self.assertFalse(SyncMock.called)

    def test_sync_not_custom_account(self):
        account = accounts.sync_account_from_stripe_data(
            self.not_custom_account_data
        )
        self.assertNotEqual(account.type, "custom")
        self.assert_common_attributes(account)

    def test_deauthorize_account(self):
        account = accounts.sync_account_from_stripe_data(
            self.not_custom_account_data
        )
        accounts.deauthorize(account)
        self.assertFalse(account.authorized)


class BankAccountsSyncTestCase(TestCase):

    def setUp(self):
        self.data = json.loads(
            """{
  "id": "ba_19VZfo2m3chDH8uLo0r6WCia",
  "object": "bank_account",
  "account": "acct_102t2K2m3chDH8uL",
  "account_holder_name": "Jane Austen",
  "account_holder_type": "individual",
  "bank_name": "STRIPE TEST BANK",
  "country": "US",
  "currency": "cad",
  "default_for_currency": false,
  "fingerprint": "ObHHcvjOGrhaeWhC",
  "last4": "6789",
  "metadata": {
  },
  "routing_number": "110000000",
  "status": "new"
}
""")

    def test_sync(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="snuffle",
            email="upagus@test"
        )
        account = Account.objects.create(
            stripe_id="acct_102t2K2m3chDH8uL",
            type="custom",
            user=user
        )
        bankaccount = externalaccounts.sync_bank_account_from_stripe_data(
            self.data
        )
        self.assertEqual(bankaccount.account_holder_name, "Jane Austen")
        self.assertEqual(bankaccount.account, account)

    @patch("pinax.stripe.actions.externalaccounts.sync_bank_account_from_stripe_data")
    def test_create_bank_account(self, SyncMock):
        account = Mock()
        externalaccounts.create_bank_account(account, 123455, "US", "usd")
        self.assertTrue(account.external_accounts.create.called)
        self.assertTrue(SyncMock.called)
