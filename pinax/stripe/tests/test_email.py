import decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from mock import patch

from ..actions import charges
from ..models import Customer


class EmailReceiptTest(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="patrick", email="user@test.com")
        self.customer = Customer.objects.create(
            user=self.user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )

    @patch("stripe.Charge.create")
    def test_email_receipt_renders_amount_properly(self, ChargeMock):
        ChargeMock.return_value = {
            "id": "ch_XXXXXX",
            "source": {
                "id": "card_01"
            },
            "amount": 40000,
            "currency": "usd",
            "paid": True,
            "refunded": False,
            "invoice": None,
            "captured": True,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        charges.create(
            customer=self.customer,
            amount=decimal.Decimal("400.00")
        )
        self.assertTrue("$400.00" in mail.outbox[0].body)

    @patch("stripe.Charge.create")
    def test_email_receipt_renders_amount_in_JPY_properly(self, ChargeMock):
        ChargeMock.return_value = {
            "id": "ch_XXXXXX",
            "source": {
                "id": "card_01"
            },
            "amount": 40000,
            "currency": "jpy",
            "paid": True,
            "refunded": False,
            "invoice": None,
            "captured": True,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        charges.create(
            customer=self.customer,
            amount=decimal.Decimal("40000"),
            currency="jpy"
        )
        self.assertTrue("$40000.00" in mail.outbox[0].body)
