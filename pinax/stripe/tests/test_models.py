from django.test import TestCase
from django.utils import timezone

from ..models import Event, EventProcessingException


class ModelTests(TestCase):

    def test_event_processing_exception_str(self):
        e = EventProcessingException(data="hello", message="hi there", traceback="fake")
        self.assertTrue("Event=" in str(e))

    def test_event_str_and_repr(self):
        created_at = timezone.now()
        created_at_iso = created_at.replace(microsecond=0).isoformat()
        e = Event(kind="customer.deleted", message={}, created_at=created_at)
        self.assertTrue("customer.deleted" in str(e))
        self.assertEqual(
            repr(e),
            f"Event(pk=None, kind='customer.deleted', customer='', created_at={created_at_iso}, stripe_id='')"
        )

        e.stripe_id = "evt_X"
        e.customer_id = "cus_YYY"
        self.assertEqual(
            repr(e),
            f"Event(pk=None, kind='customer.deleted', customer='{e.customer_id}', created_at={created_at_iso}, stripe_id='evt_X')"
        )
