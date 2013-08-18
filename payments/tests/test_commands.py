from django.core import management
from django.test import TestCase

from mock import patch

from ..utils import get_user_model


class InitCustomerTests(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="patrick")

    @patch("stripe.Customer.retrieve")
    @patch("stripe.Customer.create")
    def test_init_customer_creates_customer(self, CreateMock, RetrieveMock):  # pylint: disable=C0301
        CreateMock.return_value.id = "cus_XXXXX"
        management.call_command("init_customers")
        self.assertEquals(self.user.customer.stripe_id, "cus_XXXXX")


class init_plans(TestCase):

    @patch("stripe.Plan.create")
    def test_plans_create(self, CreateMock):
        management.call_command("init_plans")
        self.assertEquals(CreateMock.call_count, 3)
        _, _, kwargs = CreateMock.mock_calls[0]
        self.assertEqual(kwargs["id"], "entry-monthly")
        self.assertEqual(kwargs["amount"], 954)
        _, _, kwargs = CreateMock.mock_calls[1]
        self.assertEqual(kwargs["id"], "pro-monthly")
        self.assertEqual(kwargs["amount"], 1999)
        _, _, kwargs = CreateMock.mock_calls[2]
        self.assertEqual(kwargs["id"], "premium-monthly")
        self.assertEqual(kwargs["amount"], 5999)
