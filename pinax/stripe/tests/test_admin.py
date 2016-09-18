import datetime

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django.utils import timezone

from ..models import Customer, Invoice, Plan, Subscription


User = get_user_model()


class AdminTestCase(TestCase):

    def setUp(self):
        # create customers and current subscription records
        period_start = datetime.datetime(2013, 4, 1, tzinfo=timezone.utc)
        period_end = datetime.datetime(2013, 4, 30, tzinfo=timezone.utc)
        start = datetime.datetime(2013, 1, 1, tzinfo=timezone.utc)
        self.plan = Plan.objects.create(
            stripe_id="p1",
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )
        self.plan2 = Plan.objects.create(
            stripe_id="p2",
            amount=5,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Light"
        )
        for i in range(10):
            customer = Customer.objects.create(
                user=User.objects.create_user(username="patrick{0}".format(i)),
                stripe_id="cus_xxxxxxxxxxxxxx{0}".format(i)
            )
            Subscription.objects.create(
                stripe_id="sub_{}".format(i),
                customer=customer,
                plan=self.plan,
                current_period_start=period_start,
                current_period_end=period_end,
                status="active",
                start=start,
                quantity=1
            )
        customer = Customer.objects.create(
            user=User.objects.create_user(username="patrick{0}".format(11)),
            stripe_id="cus_xxxxxxxxxxxxxx{0}".format(11)
        )
        Subscription.objects.create(
            stripe_id="sub_{}".format(11),
            customer=customer,
            plan=self.plan,
            current_period_start=period_start,
            current_period_end=period_end,
            status="canceled",
            canceled_at=period_end,
            start=start,
            quantity=1
        )
        customer = Customer.objects.create(
            user=User.objects.create_user(username="patrick{0}".format(12)),
            stripe_id="cus_xxxxxxxxxxxxxx{0}".format(12)
        )
        Subscription.objects.create(
            stripe_id="sub_{}".format(12),
            customer=customer,
            plan=self.plan2,
            current_period_start=period_start,
            current_period_end=period_end,
            status="active",
            start=start,
            quantity=1
        )
        Invoice.objects.create(
            customer=customer,
            date=timezone.now(),
            amount_due=100,
            subtotal=100,
            total=100,
            period_end=period_end,
            period_start=period_start
        )
        User.objects.create_superuser(
            username='admin', email='admin@test.com', password='admin')
        self.client = Client()
        self.client.login(username='admin', password='admin')

    def test_customer_admin(self):
        """Make sure we get good responses for all filter options"""
        url = reverse('admin:pinax_stripe_customer_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url + '?sub_status=active')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url + '?sub_status=cancelled')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url + '?sub_status=none')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url + '?has_card=yes')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url + '?has_card=no')
        self.assertEqual(response.status_code, 200)

    def test_invoice_admin(self):
        url = reverse('admin:pinax_stripe_invoice_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url + '?has_card=no')
        self.assertEqual(response.status_code, 200)

    def test_plan_admin(self):
        url = reverse('admin:pinax_stripe_plan_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_charge_admin(self):
        url = reverse('admin:pinax_stripe_charge_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
