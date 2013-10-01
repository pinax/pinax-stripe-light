# pylint: disable=C0301
from django.core import management
from django.test import TestCase

from mock import patch

from ..models import Customer
from ..utils import get_user_model


class CommandTests(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="patrick")

    @patch("stripe.Customer.retrieve")
    @patch("stripe.Customer.create")
    def test_init_customer_creates_customer(self, CreateMock, RetrieveMock):
        CreateMock.return_value.id = "cus_XXXXX"
        management.call_command("init_customers")
        self.assertEquals(self.user.customer.stripe_id, "cus_XXXXX")

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

    @patch("stripe.Customer.retrieve")
    @patch("payments.models.Customer.sync")
    @patch("payments.models.Customer.sync_current_subscription")
    @patch("payments.models.Customer.sync_invoices")
    @patch("payments.models.Customer.sync_charges")
    def test_sync_customers(self, SyncChargesMock, SyncInvoicesMock, SyncSubscriptionMock, SyncMock, RetrieveMock):
        user2 = get_user_model().objects.create_user(username="thomas")
        get_user_model().objects.create_user(username="altman")
        Customer.objects.create(stripe_id="cus_XXXXX", user=self.user)
        Customer.objects.create(stripe_id="cus_YYYYY", user=user2)
        management.call_command("sync_customers")
        self.assertEqual(SyncChargesMock.call_count, 2)
        self.assertEqual(SyncInvoicesMock.call_count, 2)
        self.assertEqual(SyncSubscriptionMock.call_count, 2)
        self.assertEqual(SyncMock.call_count, 2)
