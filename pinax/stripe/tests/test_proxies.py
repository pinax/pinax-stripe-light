import decimal

from django.test import TestCase

from mock import patch

from ..proxies import ChargeProxy


class ChargeProxyTests(TestCase):

    @patch("stripe.Charge.retrieve")
    def test_stripe_charge(self, RetrieveMock):
        ChargeProxy().stripe_charge
        self.assertTrue(RetrieveMock.called)

    def test_calculate_refund_amount(self):
        charge = ChargeProxy(amount=decimal.Decimal("100"), amount_refunded=decimal.Decimal("50"))
        expected = decimal.Decimal("50")
        actual = charge.calculate_refund_amount()
        self.assertEquals(expected, actual)

    def test_calculate_refund_amount_with_amount_under(self):
        charge = ChargeProxy(amount=decimal.Decimal("100"), amount_refunded=decimal.Decimal("50"))
        expected = decimal.Decimal("25")
        actual = charge.calculate_refund_amount(amount=decimal.Decimal("25"))
        self.assertEquals(expected, actual)

    def test_calculate_refund_amount_with_amount_over(self):
        charge = ChargeProxy(amount=decimal.Decimal("100"), amount_refunded=decimal.Decimal("50"))
        expected = decimal.Decimal("50")
        actual = charge.calculate_refund_amount(amount=decimal.Decimal("100"))
        self.assertEquals(expected, actual)
