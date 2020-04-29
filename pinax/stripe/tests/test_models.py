# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import sys

from django.test import TestCase

from ..models import Event, EventProcessingException

try:
    _str = unicode
except NameError:
    _str = str

PY2 = sys.version_info[0] == 2


class ModelTests(TestCase):

    def test_event_processing_exception_str(self):
        e = EventProcessingException(data="hello", message="hi there", traceback="fake")
        self.assertTrue("Event=" in str(e))

    def test_event_str_and_repr(self):
        created_at = datetime.datetime.utcnow()
        created_at_iso = created_at.replace(microsecond=0).isoformat()
        e = Event(kind="customer.deleted", webhook_message={}, created_at=created_at)
        self.assertTrue("customer.deleted" in str(e))
        if PY2:
            self.assertEqual(repr(e), "Event(pk=None, kind=u'customer.deleted', customer=u'', valid=None, created_at={!s}, stripe_id=u'')".format(
                created_at_iso))
        else:
            self.assertEqual(repr(e), "Event(pk=None, kind='customer.deleted', customer='', valid=None, created_at={!s}, stripe_id='')".format(
                created_at_iso))

        e.stripe_id = "evt_X"
        e.customer_id = "cus_YYY"
        if PY2:
            self.assertEqual(repr(e), "Event(pk=None, kind=u'customer.deleted', customer={!r}, valid=None, created_at={!s}, stripe_id=u'evt_X')".format(
                e.customer_id, created_at_iso))
        else:
            self.assertEqual(repr(e), "Event(pk=None, kind='customer.deleted', customer={!r}, valid=None, created_at={!s}, stripe_id='evt_X')".format(
                e.customer_id, created_at_iso))
