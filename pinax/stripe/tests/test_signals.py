from django.test import TestCase

from ..signals import WEBHOOK_SIGNALS


class TestSignals(TestCase):
    def test_signals(self):
        self.assertGreater(len(WEBHOOK_SIGNALS.keys()), 100)
