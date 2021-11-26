from unittest.mock import patch

from django.test import RequestFactory, TestCase

from ..models import Event
from ..views import Webhook
from . import PLAN_CREATED_TEST_DATA


class WebhookViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("pinax.stripe.views.registry")
    def test_send_webhook(self, mock_registry):
        request = self.factory.post("/webhook", data=PLAN_CREATED_TEST_DATA, content_type="application/json")
        response = Webhook.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Event.objects.filter(stripe_id=PLAN_CREATED_TEST_DATA["id"]).exists())
        self.assertTrue(
            mock_registry.get.return_value.return_value.process.called
        )

    @patch("pinax.stripe.views.registry")
    def test_send_webhook_no_handler(self, mock_registry):
        mock_registry.get.return_value = None
        request = self.factory.post("/webhook", data=PLAN_CREATED_TEST_DATA, content_type="application/json")
        response = Webhook.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Event.objects.filter(stripe_id=PLAN_CREATED_TEST_DATA["id"]).exists())
