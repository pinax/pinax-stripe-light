import datetime

from django.test import TestCase

from ..models import Event, EventProcessingException


class ModelTests(TestCase):

    def test_event_processing_exception_str(self):
        e = EventProcessingException(data="hello", message="hi there", traceback="fake")
        self.assertTrue("Event=" in str(e))

    def test_event_str_and_repr(self):
        created_at = datetime.datetime.utcnow()
        created_at_iso = created_at.replace(microsecond=0).isoformat()
        e = Event(kind="customer.deleted", webhook_message={}, created_at=created_at)
        self.assertTrue("customer.deleted" in str(e))
        self.assertEqual(
            repr(e),
            f"Event(pk=None, kind='customer.deleted', customer='', valid=None, created_at={created_at_iso}, stripe_id='')"
        )

        e.stripe_id = "evt_X"
        e.customer_id = "cus_YYY"
        self.assertEqual(
            repr(e),
            f"Event(pk=None, kind='customer.deleted', customer='{e.customer_id}', valid=None, created_at={created_at_iso}, stripe_id='evt_X')"
        )

    def test_validated_message(self):
        created_at = datetime.datetime.utcnow()
        e = Event(kind="customer.deleted", webhook_message={}, validated_message={"foo": "bar"}, created_at=created_at)
        self.assertEqual(e.message, e.validated_message)
