from __future__ import unicode_literals

import datetime
import decimal
import sys

from django.test import TestCase
from django.utils import timezone

from mock import patch

from ..models import Charge, Customer, Event, EventProcessingException, Invoice, InvoiceItem, Plan, Subscription


def _str(obj):
    if sys.version_info < (3, 0):
        return str(obj).decode("utf-8")
    else:
        return str(obj)


class ModelTests(TestCase):

    def test_plan_str(self):
        p = Plan(amount=decimal.Decimal("5"), name="My Plan", interval="monthly", interval_count=1)
        self.assertTrue(p.name in _str(p))

    def test_plan_str_usd(self):
        p = Plan(amount=decimal.Decimal("5"), name="My Plan", currency="usd", interval="monthly", interval_count=1)
        self.assertTrue(u"\u0024" in _str(p))

    def test_plan_str_jpy(self):
        p = Plan(amount=decimal.Decimal("5"), name="My Plan", currency="jpy", interval="monthly", interval_count=1)
        self.assertTrue(u"\u00a5" in _str(p))

    def test_event_processing_exception_str(self):
        e = EventProcessingException(data="hello", message="hi there", traceback="fake")
        self.assertTrue("Event=" in str(e))

    def test_event_str(self):
        e = Event(kind="customer.deleted", webhook_message={})
        self.assertTrue("customer.deleted" in str(e))

    def test_customer_str(self):
        e = Customer()
        self.assertTrue("None" in str(e))

    def test_plan_display_invoiceitem(self):
        p = Plan(amount=decimal.Decimal("5"), name="My Plan", interval="monthly", interval_count=1)
        p.save()
        i = InvoiceItem(plan=p)
        self.assertEquals(i.plan_display(), "My Plan")

    def test_model_table_name(self):
        self.assertEquals(Customer()._meta.db_table, "pinax_stripe_customer")

    def test_event_message(self):
        event = Event(validated_message={"foo": 1})
        self.assertEquals(event.validated_message, event.message)

    def test_invoice_status(self):
        self.assertEquals(Invoice(paid=True).status, "Paid")

    def test_invoice_status_not_paid(self):
        self.assertEquals(Invoice(paid=False).status, "Open")

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

    @patch("stripe.Customer.retrieve")
    def test_stripe_subscription(self, RetrieveMock):
        Subscription(customer=Customer(stripe_id="foo")).stripe_subscription
        self.assertTrue(RetrieveMock().subscriptions.retrieve.called)
