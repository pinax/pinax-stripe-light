# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import decimal
import sys

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.test import TestCase
from django.utils import timezone

from mock import call, patch

from ..models import (
    Account,
    BankAccount,
    Card,
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

PY2 = sys.version_info[0] == 2


class ModelTests(TestCase):

    def test_plan_str_and_repr(self):
        p = Plan(amount=decimal.Decimal("5"), name="My Plan", interval="monthly", interval_count=1)
        self.assertTrue(p.name in _str(p))
        self.assertEquals(repr(p), "Plan(pk=None, name={p.name!r}, amount=Decimal('5'), currency={p.currency!r}, interval={p.interval!r}, interval_count=1, trial_period_days=None, stripe_id={p.stripe_id!r})".format(p=p))

    def test_plan_repr_unicode(self):
        p = Plan(amount=decimal.Decimal("5"), name=u"öre", interval="monthly", interval_count=1, stripe_id=u"öre")
        if PY2:
            self.assertEquals(repr(p), "Plan(pk=None, name=u'\\xf6re', amount=Decimal('5'), currency=u'', interval=u'monthly', interval_count=1, trial_period_days=None, stripe_id=u'\\xf6re')")
        else:
            self.assertEquals(repr(p), "Plan(pk=None, name='öre', amount=Decimal('5'), currency='', interval='monthly', interval_count=1, trial_period_days=None, stripe_id='öre')")

    def test_plan_str_usd(self):
        p = Plan(amount=decimal.Decimal("5"), name="My Plan", currency="usd", interval="monthly", interval_count=1)
        self.assertTrue(u"\u0024" in _str(p))

    def test_plan_str_jpy(self):
        p = Plan(amount=decimal.Decimal("5"), name="My Plan", currency="jpy", interval="monthly", interval_count=1)
        self.assertTrue(u"\u00a5" in _str(p))

    @patch("stripe.Plan.retrieve")
    def test_plan_stripe_plan(self, RetrieveMock):
        c = Plan(stripe_id="plan")
        self.assertEqual(c.stripe_plan, RetrieveMock.return_value)
        self.assertTrue(RetrieveMock.call_args_list, [
            call("plan", stripe_account=None)])

    @patch("stripe.Plan.retrieve")
    def test_plan_stripe_plan_with_account(self, RetrieveMock):
        c = Plan(stripe_id="plan", stripe_account=Account(stripe_id="acct_A"))
        self.assertEqual(c.stripe_plan, RetrieveMock.return_value)
        self.assertTrue(RetrieveMock.call_args_list, [
            call("plan", stripe_account="acct_A")])

    def test_plan_per_account(self):
        Plan.objects.create(stripe_id="plan", amount=decimal.Decimal("100"), interval="monthly", interval_count=1)
        account = Account.objects.create(stripe_id="acct_A")
        Plan.objects.create(stripe_id="plan", stripe_account=account, amount=decimal.Decimal("100"), interval="monthly", interval_count=1)
        self.assertEquals(Plan.objects.count(), 2)

    def test_event_processing_exception_str(self):
        e = EventProcessingException(data="hello", message="hi there", traceback="fake")
        self.assertTrue("Event=" in str(e))

    def test_event_str_and_repr(self):
        created_at = datetime.datetime.utcnow()
        created_at_iso = created_at.replace(microsecond=0).isoformat()
        e = Event(kind="customer.deleted", webhook_message={}, created_at=created_at)
        self.assertTrue("customer.deleted" in str(e))
        if PY2:
            self.assertEquals(repr(e), "Event(pk=None, kind=u'customer.deleted', customer=None, valid=None, created_at={!s}, stripe_id=u'')".format(
                created_at_iso))
        else:
            self.assertEquals(repr(e), "Event(pk=None, kind='customer.deleted', customer=None, valid=None, created_at={!s}, stripe_id='')".format(
                created_at_iso))

        e.stripe_id = "evt_X"
        e.customer = Customer()
        if PY2:
            self.assertEquals(repr(e), "Event(pk=None, kind=u'customer.deleted', customer={!r}, valid=None, created_at={!s}, stripe_id=u'evt_X')".format(
                e.customer, created_at_iso))
        else:
            self.assertEquals(repr(e), "Event(pk=None, kind='customer.deleted', customer={!r}, valid=None, created_at={!s}, stripe_id='evt_X')".format(
                e.customer, created_at_iso))

    def test_customer_str_and_repr(self):
        c = Customer()
        self.assertEquals(str(c), "No User(s)")
        if PY2:
            self.assertEquals(repr(c), "Customer(pk=None, stripe_id=u'')")
        else:
            self.assertEquals(repr(c), "Customer(pk=None, stripe_id='')")

    def test_customer_with_user_str_and_repr(self):
        User = get_user_model()
        c = Customer(user=User())
        self.assertEqual(str(c), "")
        if PY2:
            self.assertEqual(repr(c), "Customer(pk=None, user=<User: >, stripe_id=u'')")
        else:
            self.assertEqual(repr(c), "Customer(pk=None, user=<User: >, stripe_id='')")

    def test_customer_saved_without_users_str(self):
        c = Customer.objects.create()
        self.assertEqual(str(c), "No User(s)")
        c.stripe_id = "cu_XXX"
        self.assertEqual(str(c), "No User(s) (cu_XXX)")

    def test_connected_customer_str_and_repr(self):
        User = get_user_model()
        user = User.objects.create()
        account = Account.objects.create(stripe_id="acc_A")
        customer = Customer.objects.create(stripe_id="cus_A", stripe_account=account)
        UserAccount.objects.create(customer=customer, user=user, account=account)
        self.assertEqual(str(customer), "")
        if PY2:
            self.assertEqual(repr(customer), "Customer(pk={c.pk}, users=<User: >, stripe_id=u'cus_A')".format(c=customer))
        else:
            self.assertEqual(repr(customer), "Customer(pk={c.pk}, users=<User: >, stripe_id='cus_A')".format(c=customer))

    def test_charge_repr(self):
        charge = Charge()
        if PY2:
            self.assertEquals(repr(charge), "Charge(pk=None, customer=None, source=u'', amount=None, captured=None, paid=None, stripe_id=u'')")
        else:
            self.assertEquals(repr(charge), "Charge(pk=None, customer=None, source='', amount=None, captured=None, paid=None, stripe_id='')")

    def test_charge_str(self):
        charge = Charge()
        self.assertEquals(str(charge), "$0 (unpaid, uncaptured)")
        charge.stripe_id = "ch_XXX"
        charge.captured = True
        charge.paid = True
        charge.amount = decimal.Decimal(5)
        self.assertEquals(str(charge), "$5")
        charge.refunded = True
        self.assertEquals(str(charge), "$5 (refunded)")

    def test_charge_total_amount(self):
        charge = Charge()
        self.assertEquals(charge.total_amount, 0)
        charge.amount = decimal.Decimal(17)
        self.assertEquals(charge.total_amount, 17)
        charge.amount_refunded = decimal.Decimal(15.5)
        self.assertEquals(charge.total_amount, 1.5)

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
        if PY2:
            self.assertEquals(repr(s), "Subscription(pk=None, customer=None, plan=None, status=u'', stripe_id=u'')")
        else:
            self.assertEquals(repr(s), "Subscription(pk=None, customer=None, plan=None, status='', stripe_id='')")
        s.customer = Customer()
        s.plan = Plan()
        s.status = "active"
        s.stripe_id = "sub_X"
        if PY2:
            self.assertEquals(
                repr(s),
                "Subscription(pk=None, customer={o.customer!r}, plan={o.plan!r}, status=u'active', stripe_id=u'sub_X')".format(o=s))
        else:
            self.assertEquals(
                repr(s),
                "Subscription(pk=None, customer={o.customer!r}, plan={o.plan!r}, status='active', stripe_id='sub_X')".format(o=s))

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
        if PY2:
            self.assertEquals(repr(a), "Account(pk=None, display_name=u'', type=None, authorized=True, stripe_id=u'')")
        else:
            self.assertEquals(repr(a), "Account(pk=None, display_name='', type=None, authorized=True, stripe_id='')")
        a.stripe_id = "acct_X"
        self.assertEquals(str(a), " - acct_X")
        if PY2:
            self.assertEquals(repr(a), "Account(pk=None, display_name=u'', type=None, authorized=True, stripe_id=u'acct_X')")
        else:
            self.assertEquals(repr(a), "Account(pk=None, display_name='', type=None, authorized=True, stripe_id='acct_X')")
        a.display_name = "Display name"
        a.authorized = False
        self.assertEquals(str(a), "Display name - acct_X")
        if PY2:
            self.assertEquals(repr(a), "Account(pk=None, display_name=u'Display name', type=None, authorized=False, stripe_id=u'acct_X')")
        else:
            self.assertEquals(repr(a), "Account(pk=None, display_name='Display name', type=None, authorized=False, stripe_id='acct_X')")

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
            "UserAccount(pk=None, user=<User: >, account={o.account!r}, customer={o.customer!r})".format(
                o=ua))

    def test_card_repr(self):
        card = Card(exp_month=1, exp_year=2000)
        self.assertEquals(repr(card), "Card(pk=None, customer=None)")

        card.customer = Customer.objects.create()
        card.save()
        self.assertEquals(repr(card), "Card(pk={c.pk}, customer={c.customer!r})".format(c=card))

    def test_blank_with_null(self):
        import inspect
        import pinax.stripe.models

        clsmembers = inspect.getmembers(pinax.stripe.models, inspect.isclass)
        classes = [x[1] for x in clsmembers
                   if issubclass(x[1], models.Model)]

        for klass in classes[0:1]:
            for f in klass._meta.fields:
                if f.null:
                    self.assertTrue(f.blank, msg="%s.%s should be blank=True" % (klass.__name__, f.name))


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
