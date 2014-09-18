# pylint: disable=C0301
import decimal
import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone
from django.utils.encoding import smart_str

import stripe

from mock import patch

from ..models import Customer, CurrentSubscription
from ..utils import get_user_model
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


class AjaxViewsTests(TestCase):

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
        CurrentSubscription.objects.create(
            customer=customer,
            plan="pro",
            quantity=1,
            start=timezone.now(),
            status="active",
            cancel_at_period_end=False,
            amount=decimal.Decimal("19.99")
        )

    @patch("payments.models.Customer.update_card")
    @patch("payments.models.Customer.send_invoice")
    @patch("payments.models.Customer.retry_unpaid_invoices")
    def test_change_card(self, retry_mock, send_mock, update_mock):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("payments_ajax_change_card"),
            {"stripe_token": "XXXXX"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(update_mock.call_count, 1)
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(retry_mock.call_count, 1)
        self.assertEqual(response.status_code, 200)

    @patch("payments.models.Customer.update_card")
    @patch("payments.models.Customer.send_invoice")
    @patch("payments.models.Customer.retry_unpaid_invoices")
    def test_change_card_error(self, retry_mock, send_mock, update_mock):
        update_mock.side_effect = stripe.CardError("Bad card", "Param", "CODE")
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("payments_ajax_change_card"),
            {"stripe_token": "XXXXX"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(update_mock.call_count, 1)
        self.assertEqual(send_mock.call_count, 0)
        self.assertEqual(retry_mock.call_count, 0)
        self.assertEqual(response.status_code, 200)

    @patch("payments.models.Customer.update_card")
    @patch("payments.models.Customer.send_invoice")
    @patch("payments.models.Customer.retry_unpaid_invoices")
    def test_change_card_no_invoice(self, retry_mock, send_mock, update_mock):
        self.user.customer.card_fingerprint = "XXXXXX"
        self.user.customer.save()
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("payments_ajax_change_card"),
            {"stripe_token": "XXXXX"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(update_mock.call_count, 1)
        self.assertEqual(send_mock.call_count, 0)
        self.assertEqual(retry_mock.call_count, 1)
        self.assertEqual(response.status_code, 200)

    @patch("payments.models.Customer.subscribe")
    def test_change_plan_with_subscription(self, subscribe_mock):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("payments_ajax_change_plan"),
            {"plan": "premium"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(subscribe_mock.call_count, 1)
        self.assertEqual(response.status_code, 200)

    @patch("payments.models.Customer.subscribe")
    def test_change_plan_no_subscription(self, subscribe_mock):
        self.user.customer.current_subscription.delete()
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("payments_ajax_change_plan"),
            {"plan": "premium"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(subscribe_mock.call_count, 1)
        self.assertEqual(response.status_code, 200)

    @patch("payments.models.Customer.subscribe")
    def test_change_plan_invalid_form(self, subscribe_mock):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("payments_ajax_change_plan"),
            {"plan": "not-valid"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(subscribe_mock.call_count, 0)
        self.assertEqual(response.status_code, 200)

    @patch("payments.models.Customer.subscribe")
    def test_change_plan_stripe_error(self, subscribe_mock):
        subscribe_mock.side_effect = stripe.StripeError(
            "Bad card",
            "Param",
            "CODE"
        )
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("payments_ajax_change_plan"),
            {"plan": "premium"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(subscribe_mock.call_count, 1)
        self.assertEqual(response.status_code, 200)

    @patch("payments.models.Customer.subscribe")
    @patch("payments.models.Customer.update_card")
    @patch("payments.models.Customer.create")
    def test_subscribe(self, create_cus_mock, upd_card_mock, subscribe_mock):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("payments_ajax_subscribe"),
            {"plan": "premium", "stripe_token": "XXXXX"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(create_cus_mock.call_count, 0)
        self.assertEqual(upd_card_mock.call_count, 1)
        self.assertEqual(subscribe_mock.call_count, 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(smart_str(response.content))["location"],  # pylint: disable=E1103
            reverse("payments_history")
        )

    @patch("payments.models.Customer.subscribe")
    @patch("payments.models.Customer.update_card")
    @patch("payments.models.Customer.create")
    def test_subscribe_no_customer(self, create_cus_mock, upd_card_mock, subscribe_mock):
        self.client.login(username=self.user.username, password=self.password)
        Customer.objects.all().delete()
        response = self.client.post(
            reverse("payments_ajax_subscribe"),
            {"plan": "premium", "stripe_token": "XXXXX"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(create_cus_mock.call_count, 1)
        self.assertEqual(
            json.loads(smart_str(response.content))["location"],  # pylint: disable=E1103
            reverse("payments_history")
        )

    @patch("payments.models.Customer.subscribe")
    @patch("payments.models.Customer.update_card")
    @patch("payments.models.Customer.create")
    def test_subscribe_error(self, create_cus_mock, upd_card_mock, subscribe_mock):
        self.client.login(username=self.user.username, password=self.password)
        upd_card_mock.side_effect = stripe.StripeError("foo")
        response = self.client.post(
            reverse("payments_ajax_subscribe"),
            {"plan": "premium", "stripe_token": "XXXXX"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(create_cus_mock.call_count, 0)
        self.assertEqual(upd_card_mock.call_count, 1)
        self.assertEqual(subscribe_mock.call_count, 0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'foo')

    def test_subscribe_invalid_form_data(self):
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("payments_ajax_subscribe"),
            {},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.context['error'],
                         {'plan': ['This field is required.']})

    @patch("payments.models.Customer.cancel")
    def test_cancel(self, cancel_mock):
        self.client.login(username=self.user.username, password=self.password)
        self.client.post(
            reverse("payments_ajax_cancel"),
            {},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(cancel_mock.call_count, 1)

    @patch("payments.models.Customer.cancel")
    def test_cancel_error(self, cancel_mock):
        cancel_mock.side_effect = stripe.StripeError("foo")
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.post(
            reverse("payments_ajax_cancel"),
            {},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(cancel_mock.call_count, 1)
        self.assertEqual(response.context['error'], 'foo')
