import decimal

from django.test import TestCase

from ..models import Plan, EventProcessingException, Event, Customer, InvoiceItem


class ModelTests(TestCase):

    def test_plan_str(self):
        p = Plan(amount=decimal.Decimal("5"), name="My Plan", interval="monthly", interval_count=1)
        self.assertTrue(p.name in str(p))

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
