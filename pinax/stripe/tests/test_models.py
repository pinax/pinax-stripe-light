from __future__ import unicode_literals

import datetime
import decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from mock import patch

from ..models import (
    Account,
    BankAccount,
    Charge,
    Coupon,
    Customer,
    Event,
    EventProcessingException,
    Invoice,
    InvoiceItem,
    Plan,
    Subscription,
    Transfer,
    UserAccount
)

try:
    _str = unicode
except NameError:
    _str = str


class ModelTests(TestCase):

    def test_plan_str_and_repr(self):
        p = Plan(amount=decimal.Decimal("5"), name="My Plan", interval="monthly", interval_count=1)
        self.assertTrue(p.name in _str(p))
        self.assertEquals(repr(p), "Plan(pk=None, name='My Plan', amount=Decimal('5'), currency='', interval='monthly', interval_count=1, trial_period_days=None, stripe_id='')")

    def test_plan_str_usd(self):
        p = Plan(amount=decimal.Decimal("5"), name="My Plan", currency="usd", interval="monthly", interval_count=1)
        self.assertTrue(u"\u0024" in _str(p))

    def test_plan_str_jpy(self):
        p = Plan(amount=decimal.Decimal("5"), name="My Plan", currency="jpy", interval="monthly", interval_count=1)
        self.assertTrue(u"\u00a5" in _str(p))

    def test_event_processing_exception_str(self):
        e = EventProcessingException(data="hello", message="hi there", traceback="fake")
        self.assertTrue("Event=" in str(e))

    def test_event_str_and_repr(self):
        e = Event(kind="customer.deleted", webhook_message={})
        self.assertTrue("customer.deleted" in str(e))
        self.assertEquals(repr(e), "Event(pk=None, kind='customer.deleted', customer=None, valid=None, stripe_id='')")

        e.stripe_id = "evt_X"
        e.customer = Customer()
        self.assertEquals(repr(e), "Event(pk=None, kind='customer.deleted', customer={!r}, valid=None, stripe_id='{}')".format(
            e.customer, e.stripe_id))

    def test_customer_str_and_repr(self):
        c = Customer()
        self.assertTrue("None" in str(c))
        self.assertEquals(repr(c), "Customer(pk=None, user=None, stripe_id='')")

    def test_charge_repr(self):
        charge = Charge()
        self.assertEquals(repr(charge), "Charge(customer=None, source='', amount=None, captured=None, paid=None, stripe_id='')")

    def test_plan_display_invoiceitem(self):
        p = Plan(amount=decimal.Decimal("5"), name="My Plan", interval="monthly", interval_count=1)
        p.save()
        i = InvoiceItem(plan=p)
        self.assertEquals(i.plan_display(), "My Plan")

    def test_coupon_percent(self):
        c = Coupon(percent_off=25, duration="repeating", duration_in_months=3)
        self.assertEquals(str(c), "Coupon for 25% off, repeating")

    def test_coupon_absolute(self):
        c = Coupon(amount_off=decimal.Decimal(50.00), duration="once", currency="usd")
        self.assertEquals(str(c), "Coupon for $50, once")

    def test_model_table_name(self):
        self.assertEquals(Customer()._meta.db_table, "pinax_stripe_customer")

    def test_event_message(self):
        event = Event(validated_message={"foo": 1})
        self.assertEquals(event.validated_message, event.message)

    def test_invoice_status(self):
        self.assertEquals(Invoice(paid=True).status, "Paid")

    def test_invoice_status_not_paid(self):
        self.assertEquals(Invoice(paid=False).status, "Open")

    def test_subscription_repr(self):
        s = Subscription()
        self.assertEquals(repr(s), "Subscription(pk=None, customer=None, plan=None, status='', stripe_id='')")
        s.customer = Customer()
        s.plan = Plan()
        s.status = "active"
        s.stripe_id = "sub_X"
        self.assertEquals(
            repr(s),
            "Subscription(pk=None, customer={!r}, plan={!r}, status='active', stripe_id='sub_X')".format(
                s.customer,
                s.plan,
            ))

    def test_subscription_total_amount(self):
        sub = Subscription(plan=Plan(name="Pro Plan", amount=decimal.Decimal("100")), quantity=2)
        self.assertEquals(sub.total_amount, decimal.Decimal("200"))

    def test_subscription_plan_display(self):
        sub = Subscription(plan=Plan(name="Pro Plan"))
        self.assertEquals(sub.plan_display(), "Pro Plan")

    def test_subscription_status_display(self):
        sub = Subscription(status="overly_active")
        self.assertEquals(sub.status_display(), "Overly Active")

    def test_subscription_delete(self):
        plan = Plan.objects.create(stripe_id="pro2", amount=decimal.Decimal("100"), interval="monthly", interval_count=1)
        customer = Customer.objects.create(stripe_id="foo")
        sub = Subscription.objects.create(customer=customer, status="trialing", start=timezone.now(), plan=plan, quantity=1, cancel_at_period_end=True, current_period_end=(timezone.now() - datetime.timedelta(days=2)))
        sub.delete()
        self.assertIsNone(sub.status)
        self.assertEquals(sub.quantity, 0)
        self.assertEquals(sub.amount, 0)

    def test_account_str_and_repr(self):
        a = Account()
        self.assertEquals(str(a), " - ")
        self.assertEquals(repr(a), "Account(pk=None, display_name='', type=None, stripe_id='', authorized=True)")
        a.stripe_id = "acct_X"
        self.assertEquals(str(a), " - acct_X")
        self.assertEquals(repr(a), "Account(pk=None, display_name='', type=None, stripe_id='acct_X', authorized=True)")
        a.display_name = "Display name"
        a.authorized = False
        self.assertEquals(str(a), "Display name - acct_X")
        self.assertEquals(repr(a), "Account(pk=None, display_name='Display name', type=None, stripe_id='acct_X', authorized=False)")

    @patch("stripe.Subscription.retrieve")
    def test_subscription_stripe_subscription_with_connnect(self, RetrieveMock):
        a = Account(stripe_id="acc_X")
        c = Customer(stripe_id="cus_X", stripe_account=a)
        s = Subscription(stripe_id="sub_X", customer=c)
        s.stripe_subscription
        RetrieveMock.assert_called_once_with("sub_X", stripe_account="acc_X")

    def test_customer_required_fields(self):
        c = Customer(stripe_id="cus_A")
        c.full_clean()

    def test_user_account_validation(self):
        User = get_user_model()
        a = Account()
        ua = UserAccount(user=User(), account=a, customer=Customer(stripe_account=Account()))
        with self.assertRaises(ValidationError):
            ua.clean()

    def test_user_account_repr(self):
        User = get_user_model()
        ua = UserAccount(user=User(), account=Account(), customer=Customer())
        self.assertEquals(
            repr(ua),
            "UserAccount(pk=None, user=<User: >, account=Account(pk=None, display_name='', type=None, stripe_id='', authorized=True)"
            ", customer=Customer(pk=None, user=None, stripe_id=''))")


class StripeObjectTests(TestCase):

    @patch("stripe.Charge.retrieve")
    def test_stripe_charge(self, RetrieveMock):
        Charge().stripe_charge
        self.assertTrue(RetrieveMock.called)

    @patch("stripe.Customer.retrieve")
    def test_stripe_customer(self, RetrieveMock):
        Customer().stripe_customer
        self.assertTrue(RetrieveMock.called)

    @patch("stripe.Invoice.retrieve")
    def test_stripe_invoice(self, RetrieveMock):
        Invoice().stripe_invoice
        self.assertTrue(RetrieveMock.called)

    @patch("stripe.Subscription.retrieve")
    def test_stripe_subscription(self, RetrieveMock):
        Subscription(stripe_id="sub_X", customer=Customer(stripe_id="foo")).stripe_subscription
        RetrieveMock.assert_called_once_with("sub_X", stripe_account=None)

    @patch("stripe.Transfer.retrieve")
    def test_stripe_transfer(self, RetrieveMock):
        Transfer(amount=10).stripe_transfer
        self.assertTrue(RetrieveMock.called)

    @patch("stripe.Account.retrieve")
    def test_stripe_bankaccount(self, RetrieveMock):
        BankAccount(account=Account(stripe_id="foo")).stripe_bankaccount
        self.assertTrue(RetrieveMock.return_value.external_accounts.retrieve.called)
