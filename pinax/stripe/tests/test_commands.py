import decimal

from django.core import management
from django.test import TestCase

from django.contrib.auth import get_user_model
from stripe.error import InvalidRequestError

from mock import patch

from ..models import Customer, Plan


class CommandTests(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="patrick")

    @patch("stripe.Customer.retrieve")
    @patch("stripe.Customer.create")
    def test_init_customer_creates_customer(self, CreateMock, RetrieveMock):
        CreateMock.return_value = dict(
            account_balance=0,
            delinquent=False,
            default_source="card_178Zqj2eZvKYlo2Cr2fUZZz7",
            currency="usd",
            id="cus_XXXXX",
            sources=dict(data=[]),
            subscriptions=dict(data=[]),
        )
        management.call_command("init_customers")
        customer = Customer.objects.get(user=self.user)
        self.assertEquals(customer.stripe_id, "cus_XXXXX")

    @patch("stripe.Plan.all")
    @patch("stripe.Plan.auto_paging_iter", create=True, side_effect=AttributeError)
    def test_plans_create_deprecated(self, PlanAutoPagerMock, PlanAllMock):
        PlanAllMock().data = [{
            "id": "entry-monthly",
            "amount": 954,
            "interval": "monthly",
            "interval_count": 1,
            "currency": None,
            "statement_descriptor": None,
            "trial_period_days": None,
            "name": "Pro",
            "metadata": {}
        }]
        management.call_command("sync_plans")
        self.assertEquals(Plan.objects.count(), 1)
        self.assertEquals(Plan.objects.all()[0].stripe_id, "entry-monthly")
        self.assertEquals(Plan.objects.all()[0].amount, decimal.Decimal("9.54"))

    @patch("stripe.Plan.auto_paging_iter", create=True)
    def test_plans_create(self, PlanAutoPagerMock):
        PlanAutoPagerMock.return_value = [{
            "id": "entry-monthly",
            "amount": 954,
            "interval": "monthly",
            "interval_count": 1,
            "currency": None,
            "statement_descriptor": None,
            "trial_period_days": None,
            "name": "Pro",
            "metadata": {}
        }]
        management.call_command("sync_plans")
        self.assertEquals(Plan.objects.count(), 1)
        self.assertEquals(Plan.objects.all()[0].stripe_id, "entry-monthly")
        self.assertEquals(Plan.objects.all()[0].amount, decimal.Decimal("9.54"))

    @patch("stripe.Customer.retrieve")
    @patch("pinax.stripe.actions.customers.sync_customer")
    @patch("pinax.stripe.actions.invoices.sync_invoices_for_customer")
    @patch("pinax.stripe.actions.charges.sync_charges_for_customer")
    def test_sync_customers(self, SyncChargesMock, SyncInvoicesMock, SyncMock, RetrieveMock):
        user2 = get_user_model().objects.create_user(username="thomas")
        get_user_model().objects.create_user(username="altman")
        Customer.objects.create(stripe_id="cus_XXXXX", user=self.user)
        Customer.objects.create(stripe_id="cus_YYYYY", user=user2)
        management.call_command("sync_customers")
        self.assertEqual(SyncChargesMock.call_count, 2)
        self.assertEqual(SyncInvoicesMock.call_count, 2)
        self.assertEqual(SyncMock.call_count, 2)

    @patch("stripe.Customer.retrieve")
    @patch("pinax.stripe.actions.customers.sync_customer")
    @patch("pinax.stripe.actions.invoices.sync_invoices_for_customer")
    @patch("pinax.stripe.actions.charges.sync_charges_for_customer")
    def test_sync_customers_with_test_customer(self, SyncChargesMock, SyncInvoicesMock, SyncMock, RetrieveMock):
        user2 = get_user_model().objects.create_user(username="thomas")
        get_user_model().objects.create_user(username="altman")
        Customer.objects.create(stripe_id="cus_XXXXX", user=self.user)
        Customer.objects.create(stripe_id="cus_YYYYY", user=user2)

        SyncMock.side_effect = InvalidRequestError('Unknown customer', None, http_status=404)

        management.call_command("sync_customers")
        self.assertEqual(SyncChargesMock.call_count, 0)
        self.assertEqual(SyncInvoicesMock.call_count, 0)
        self.assertEqual(SyncMock.call_count, 2)
