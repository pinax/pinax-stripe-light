
from django.test import TestCase

from ..views import SubscribeView


class PaymentsContextMixinTests(TestCase):

    def test_payments_context_mixin_get_context_data(self):
        data = SubscribeView().get_context_data()
        self.assertTrue("STRIPE_PUBLIC_KEY" in data)
        self.assertTrue("PLAN_CHOICES" in data)
        self.assertTrue("PAYMENT_PLANS" in data)


class SubscribeViewTests(TestCase):

    def test_payments_context_mixin_get_context_data(self):
        data = SubscribeView().get_context_data()
        self.assertTrue("form" in data)
