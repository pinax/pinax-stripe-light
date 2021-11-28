from unittest.mock import patch

from django.test import RequestFactory, TestCase

import stripe

from ..models import Event
from ..views import Webhook
from . import PLAN_CREATED_TEST_DATA


class WebhookViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("pinax.stripe.views.stripe.Webhook.construct_event")
    @patch("pinax.stripe.views.registry")
    def test_send_webhook(self, mock_registry, mock_event):
        mock_event.return_value.to_dict_recursive.return_value = PLAN_CREATED_TEST_DATA
        request = self.factory.post("/webhook", data=PLAN_CREATED_TEST_DATA, content_type="application/json", HTTP_STRIPE_SIGNATURE="foo")
        response = Webhook.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Event.objects.filter(stripe_id=PLAN_CREATED_TEST_DATA["id"]).exists())
        self.assertTrue(
            mock_registry.get.return_value.return_value.process.called
        )

    @patch("pinax.stripe.views.stripe.Webhook.construct_event")
    @patch("pinax.stripe.views.registry")
    def test_send_webhook_dupe(self, mock_registry, mock_event):
        Event.objects.create(stripe_id=PLAN_CREATED_TEST_DATA["id"], message=PLAN_CREATED_TEST_DATA)
        mock_event.return_value.to_dict_recursive.return_value = PLAN_CREATED_TEST_DATA
        mock_event.return_value.id = PLAN_CREATED_TEST_DATA["id"]
        request = self.factory.post("/webhook", data=PLAN_CREATED_TEST_DATA, content_type="application/json", HTTP_STRIPE_SIGNATURE="foo")
        response = Webhook.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            mock_registry.get.return_value.return_value.process.called
        )

    @patch("pinax.stripe.views.stripe.Webhook.construct_event")
    @patch("pinax.stripe.views.registry")
    def test_send_webhook_no_handler(self, mock_registry, mock_event):
        mock_registry.get.return_value = None
        mock_event.return_value.to_dict_recursive.return_value = PLAN_CREATED_TEST_DATA
        request = self.factory.post("/webhook", data=PLAN_CREATED_TEST_DATA, content_type="application/json", HTTP_STRIPE_SIGNATURE="foo")
        response = Webhook.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Event.objects.filter(stripe_id=PLAN_CREATED_TEST_DATA["id"]).exists())

    @patch("pinax.stripe.views.stripe.Webhook.construct_event")
    @patch("pinax.stripe.views.registry")
    def test_send_webhook_value_error(self, mock_registry, mock_event):
        mock_registry.get.return_value = None
        mock_event.side_effect = ValueError
        request = self.factory.post("/webhook", data=PLAN_CREATED_TEST_DATA, content_type="application/json", HTTP_STRIPE_SIGNATURE="foo")
        response = Webhook.as_view()(request)
        self.assertEqual(response.status_code, 400)

    @patch("pinax.stripe.views.stripe.Webhook.construct_event")
    @patch("pinax.stripe.views.registry")
    def test_send_webhook_stripe_error(self, mock_registry, mock_event):
        mock_registry.get.return_value = None
        mock_event.side_effect = stripe.error.SignatureVerificationError("foo", "sig")
        request = self.factory.post("/webhook", data=PLAN_CREATED_TEST_DATA, content_type="application/json", HTTP_STRIPE_SIGNATURE="foo")
        response = Webhook.as_view()(request)
        self.assertEqual(response.status_code, 400)
