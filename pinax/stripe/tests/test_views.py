from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

import stripe
from mock import patch

from ..models import Card, Customer, Invoice, Plan, Subscription
from ..views import PaymentMethodCreateView

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse


class PaymentsContextMixinTests(TestCase):

    def test_payments_context_mixin_get_context_data(self):
        data = PaymentMethodCreateView().get_context_data()
        self.assertTrue("PINAX_STRIPE_PUBLIC_KEY" in data)


class InvoiceListViewTests(TestCase):

    def setUp(self):
        self.password = "eldarion"
        self.user = get_user_model().objects.create_user(
            username="patrick",
            password=self.password
        )
        self.user.save()
        customer = Customer.objects.create(
            stripe_id="cus_1",
            user=self.user
        )
        Invoice.objects.create(
            stripe_id="inv_001",
            customer=customer,
            amount_due=100,
            period_end=timezone.now(),
            period_start=timezone.now(),
            subtotal=100,
            total=100,
            date=timezone.now()
        )
        Invoice.objects.create(
            stripe_id="inv_002",
            customer=customer,
            amount_due=50,
            period_end=timezone.now(),
            period_start=timezone.now(),
            subtotal=50,
            total=50,
            date=timezone.now()
        )

    def test_context(self):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(
            reverse("pinax_stripe_invoice_list")
        )
        self.assertTrue("invoice_list" in response.context_data)
        self.assertEquals(response.context_data["invoice_list"].count(), 2)
        self.assertEquals(response.context_data["invoice_list"][0].total, 100)
        self.assertEquals(response.context_data["invoice_list"][1].total, 50)


class PaymentMethodListViewTests(TestCase):

    def setUp(self):
        self.password = "eldarion"
        self.user = get_user_model().objects.create_user(
            username="patrick",
            password=self.password
        )
        self.user.save()
        customer = Customer.objects.create(
            stripe_id="cus_1",
            user=self.user
        )
        Card.objects.create(
            stripe_id="card_001",
            customer=customer,
            address_line_1_check="nothing",
            address_zip_check="nothing",
            country="US",
            cvc_check="passed",
            exp_month=1,
            exp_year=2020,
            funding="yes",
            fingerprint="abc"
        )

    def test_context(self):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(
            reverse("pinax_stripe_payment_method_list")
        )
        self.assertTrue("payment_method_list" in response.context_data)
        self.assertEquals(response.context_data["payment_method_list"].count(), 1)
        self.assertEquals(response.context_data["payment_method_list"][0].stripe_id, "card_001")


class PaymentMethodCreateViewTests(TestCase):

    def setUp(self):
        self.password = "eldarion"
        self.user = get_user_model().objects.create_user(
            username="patrick",
            password=self.password
        )
        self.user.save()
        Customer.objects.create(
            stripe_id="cus_1",
            user=self.user
        )

    @patch("pinax.stripe.actions.sources.create_card")
    def test_post(self, CreateMock):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_payment_method_create"),
            {}
        )
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse("pinax_stripe_payment_method_list"))

    @patch("pinax.stripe.actions.sources.create_card")
    def test_post_on_error(self, CreateMock):
        CreateMock.side_effect = stripe.error.CardError("Bad card", "Param", "CODE")
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_payment_method_create"),
            {}
        )
        self.assertEquals(response.status_code, 200)
        self.assertTrue("errors" in response.context_data)


class PaymentMethodDeleteViewTests(TestCase):

    def setUp(self):
        self.password = "eldarion"
        self.user = get_user_model().objects.create_user(
            username="patrick",
            password=self.password
        )
        self.user.save()
        customer = Customer.objects.create(
            stripe_id="cus_1",
            user=self.user
        )
        self.card = Card.objects.create(
            stripe_id="card_001",
            customer=customer,
            address_line_1_check="nothing",
            address_zip_check="nothing",
            country="US",
            cvc_check="passed",
            exp_month=1,
            exp_year=2020,
            funding="yes",
            fingerprint="abc"
        )

    @patch("pinax.stripe.actions.sources.delete_card")
    def test_post(self, CreateMock):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_payment_method_delete", args=[self.card.pk]),
            {}
        )
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse("pinax_stripe_payment_method_list"))

    @patch("pinax.stripe.actions.sources.delete_card")
    def test_post_on_error(self, CreateMock):
        CreateMock.side_effect = stripe.error.CardError("Bad card", "Param", "CODE")
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_payment_method_delete", args=[self.card.pk]),
            {}
        )
        self.assertEquals(response.status_code, 200)
        self.assertTrue("errors" in response.context_data)


class PaymentMethodUpdateViewTests(TestCase):

    def setUp(self):
        self.password = "eldarion"
        self.user = get_user_model().objects.create_user(
            username="patrick",
            password=self.password
        )
        self.user.save()
        customer = Customer.objects.create(
            stripe_id="cus_1",
            user=self.user
        )
        self.card = Card.objects.create(
            stripe_id="card_001",
            customer=customer,
            address_line_1_check="nothing",
            address_zip_check="nothing",
            country="US",
            cvc_check="passed",
            exp_month=1,
            exp_year=2020,
            funding="yes",
            fingerprint="abc"
        )

    @patch("pinax.stripe.actions.sources.update_card")
    def test_post(self, CreateMock):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_payment_method_update", args=[self.card.pk]),
            {
                "expMonth": 1,
                "expYear": 2018
            }
        )
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse("pinax_stripe_payment_method_list"))

    @patch("pinax.stripe.actions.sources.update_card")
    def test_post_invalid_form(self, CreateMock):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_payment_method_update", args=[self.card.pk]),
            {
                "expMonth": 13,
                "expYear": 2014
            }
        )
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context_data["form"].is_valid(), False)

    @patch("pinax.stripe.actions.sources.update_card")
    def test_post_on_error(self, CreateMock):
        CreateMock.side_effect = stripe.error.CardError("Bad card", "Param", "CODE")
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_payment_method_update", args=[self.card.pk]),
            {
                "expMonth": 1,
                "expYear": 2018
            }
        )
        self.assertEquals(response.status_code, 200)
        self.assertTrue("errors" in response.context_data)


class SubscriptionListViewTests(TestCase):

    def setUp(self):
        self.password = "eldarion"
        self.user = get_user_model().objects.create_user(
            username="patrick",
            password=self.password
        )
        self.user.save()
        customer = Customer.objects.create(
            stripe_id="cus_1",
            user=self.user
        )
        plan = Plan.objects.create(
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )
        Subscription.objects.create(
            stripe_id="sub_001",
            customer=customer,
            plan=plan,
            quantity=1,
            start=timezone.now(),
            status="active"
        )

    def test_context(self):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(
            reverse("pinax_stripe_subscription_list")
        )
        self.assertTrue("subscription_list" in response.context_data)
        self.assertEquals(response.context_data["subscription_list"].count(), 1)
        self.assertEquals(response.context_data["subscription_list"][0].stripe_id, "sub_001")


class SubscriptionCreateViewTests(TestCase):

    def setUp(self):
        self.password = "eldarion"
        self.user = get_user_model().objects.create_user(
            username="patrick",
            password=self.password
        )
        self.user.save()
        self.plan = Plan.objects.create(
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )

    @patch("pinax.stripe.actions.subscriptions.create")
    def test_post(self, CreateMock):
        Customer.objects.create(
            stripe_id="cus_1",
            user=self.user
        )
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_subscription_create"),
            {
                "plan": self.plan.id
            }
        )
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse("pinax_stripe_subscription_list"))

    @patch("pinax.stripe.actions.customers.create")
    @patch("pinax.stripe.actions.subscriptions.create")
    def test_post_no_prior_customer(self, CreateMock, CustomerCreateMock):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_subscription_create"),
            {
                "plan": self.plan.id
            }
        )
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse("pinax_stripe_subscription_list"))
        self.assertTrue(CustomerCreateMock.called)

    @patch("pinax.stripe.actions.sources.create_card")
    def test_post_on_error(self, CreateMock):
        Customer.objects.create(
            stripe_id="cus_1",
            user=self.user
        )
        CreateMock.side_effect = stripe.error.StripeError("Bad Mojo", "Param", "CODE")
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_subscription_create"),
            {
                "plan": self.plan.id
            }
        )
        self.assertEquals(response.status_code, 200)
        self.assertTrue("errors" in response.context_data)


class SubscriptionDeleteViewTests(TestCase):

    def setUp(self):
        self.password = "eldarion"
        self.user = get_user_model().objects.create_user(
            username="patrick",
            password=self.password
        )
        self.user.save()
        customer = Customer.objects.create(
            stripe_id="cus_1",
            user=self.user
        )
        plan = Plan.objects.create(
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )
        self.subscription = Subscription.objects.create(
            stripe_id="sub_001",
            customer=customer,
            plan=plan,
            quantity=1,
            start=timezone.now(),
            status="active"
        )

    @patch("pinax.stripe.actions.subscriptions.cancel")
    def test_post(self, CancelMock):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_subscription_delete", args=[self.subscription.pk]),
            {}
        )
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse("pinax_stripe_subscription_list"))

    @patch("pinax.stripe.actions.subscriptions.cancel")
    def test_post_on_error(self, CancelMock):
        CancelMock.side_effect = stripe.error.StripeError("Bad Foo", "Param", "CODE")
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_subscription_delete", args=[self.subscription.pk]),
            {}
        )
        self.assertEquals(response.status_code, 200)
        self.assertTrue("errors" in response.context_data)


class SubscriptionUpdateViewTests(TestCase):

    def setUp(self):
        self.password = "eldarion"
        self.user = get_user_model().objects.create_user(
            username="patrick",
            password=self.password
        )
        self.user.save()
        customer = Customer.objects.create(
            stripe_id="cus_1",
            user=self.user
        )
        plan = Plan.objects.create(
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )
        self.subscription = Subscription.objects.create(
            stripe_id="sub_001",
            customer=customer,
            plan=plan,
            quantity=1,
            start=timezone.now(),
            status="active"
        )

    def test_get(self):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(
            reverse("pinax_stripe_subscription_update", args=[self.subscription.pk])
        )
        self.assertEquals(response.status_code, 200)
        self.assertTrue("form" in response.context_data)
        self.assertTrue(response.context_data["form"].initial["plan"], self.subscription.plan)

    @patch("pinax.stripe.actions.subscriptions.update")
    def test_post(self, UpdateMock):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_subscription_update", args=[self.subscription.pk]),
            {
                "plan": self.subscription.plan.id
            }
        )
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse("pinax_stripe_subscription_list"))

    @patch("pinax.stripe.actions.subscriptions.update")
    def test_post_invalid(self, UpdateMock):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_subscription_update", args=[self.subscription.pk]),
            {
                "plan": "not a real plan"
            }
        )
        self.assertEquals(response.status_code, 200)
        self.assertTrue(len(response.context_data["form"].errors) > 0)

    @patch("pinax.stripe.actions.subscriptions.update")
    def test_post_on_error(self, UpdateMock):
        UpdateMock.side_effect = stripe.error.StripeError("Bad Foo", "Param", "CODE")
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("pinax_stripe_subscription_update", args=[self.subscription.pk]),
            {
                "plan": self.subscription.plan.id
            }
        )
        self.assertEquals(response.status_code, 200)
        self.assertTrue("errors" in response.context_data)
