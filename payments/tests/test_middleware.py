# pylint: disable=C0301
import decimal

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from django.contrib.auth import authenticate, login, logout

from mock import Mock

from ..middleware import ActiveSubscriptionMiddleware, URLS
from ..models import Customer, CurrentSubscription
from ..utils import get_user_model


class DummySession(dict):

    def cycle_key(self):
        return

    def flush(self):
        return


class ActiveSubscriptionMiddlewareTests(TestCase):

    def setUp(self):
        self.middleware = ActiveSubscriptionMiddleware()
        self.request = Mock()
        self.request.session = DummySession()
        user = get_user_model().objects.create_user(username="patrick")
        user.set_password("eldarion")
        user.save()
        user = authenticate(username="patrick", password="eldarion")
        login(self.request, user)

    def test_authed_user_with_no_customer_redirects_on_non_exempt_url(self):
        self.request.path = "/the/app/"
        response = self.middleware.process_request(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers["location"][1],  # pylint: disable=W0212
            reverse(settings.SUBSCRIPTION_REQUIRED_REDIRECT)
        )

    def test_authed_user_with_no_customer_passes_with_exempt_url(self):
        URLS.append("/accounts/signup/")
        self.request.path = "/accounts/signup/"
        response = self.middleware.process_request(self.request)
        self.assertIsNone(response)

    def test_authed_user_with_no_active_subscription_passes_with_exempt_url(self):
        Customer.objects.create(stripe_id="cus_1", user=self.request.user)
        URLS.append("/accounts/signup/")
        self.request.path = "/accounts/signup/"
        response = self.middleware.process_request(self.request)
        self.assertIsNone(response)

    def test_authed_user_with_no_active_subscription_redirects_on_non_exempt_url(self):
        Customer.objects.create(stripe_id="cus_1", user=self.request.user)
        URLS.append("/accounts/signup/")
        self.request.path = "/the/app/"
        response = self.middleware.process_request(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers["location"][1],  # pylint: disable=W0212
            reverse(settings.SUBSCRIPTION_REQUIRED_REDIRECT)
        )

    def test_authed_user_with_active_subscription_redirects_on_non_exempt_url(self):
        customer = Customer.objects.create(
            stripe_id="cus_1",
            user=self.request.user
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
        URLS.append("/accounts/signup/")
        self.request.path = "/the/app/"
        response = self.middleware.process_request(self.request)
        self.assertIsNone(response)

    def test_unauthed_user_passes(self):
        logout(self.request)
        URLS.append("/accounts/signup/")
        self.request.path = "/the/app/"
        response = self.middleware.process_request(self.request)
        self.assertIsNone(response)

    def test_staff_user_passes(self):
        self.request.user.is_staff = True
        URLS.append("/accounts/signup/")
        self.request.path = "/the/app/"
        response = self.middleware.process_request(self.request)
        self.assertIsNone(response)
