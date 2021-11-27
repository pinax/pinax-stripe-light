import json
from unittest.mock import patch

from django.dispatch import Signal
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

import stripe

from ..models import Event, EventProcessingException
from ..webhooks import (
    AccountUpdatedWebhook,
    AccountApplicationDeauthorizeWebhook,
    AccountExternalAccountCreatedWebhook,
    Webhook,
    registry
)


class NewAccountUpdatedWebhook(AccountUpdatedWebhook):
    pass


class WebhookRegistryTest(TestCase):

    def test_get_signal(self):
        signal = registry.get_signal("account.updated")
        self.assertTrue(isinstance(signal, Signal))

    def test_get_signal_keyerror(self):
        self.assertIsNone(registry.get_signal("not a webhook"))

    def test_inherited_hook(self):
        webhook = registry.get("account.updated")
        self.assertIs(webhook, NewAccountUpdatedWebhook)


class WebhookTests(TestCase):

    event_data = {
        "api_version": "2017-06-05",
        "created": 1348360173,
        "data": {
            "object": {
                "amount": 455,
                "currency": "usd",
                "date": 1348876800,
                "description": None,
                "id": "ach_XXXXXXXXXXXX",
                "object": "transfer",
                "other_transfers": [],
                "status": "pending",
                "livemode": True,
                "reversed": False,
                "summary": {
                    "adjustment_count": 0,
                    "adjustment_fee_details": [],
                    "adjustment_fees": 0,
                    "adjustment_gross": 0,
                    "charge_count": 1,
                    "charge_fee_details": [{
                        "amount": 45,
                        "application": None,
                        "currency": "usd",
                        "description": None,
                        "type": "stripe_fee"
                    }],
                    "charge_fees": 45,
                    "charge_gross": 500,
                    "collected_fee_count": 0,
                    "collected_fee_gross": 0,
                    "currency": "usd",
                    "net": 455,
                    "refund_count": 0,
                    "refund_fees": 0,
                    "refund_gross": 0,
                    "validation_count": 0,
                    "validation_fees": 0
                }
            }
        },
        "id": "evt_XXXXXXXXXXXXx",
        "livemode": True,
        "object": "event",
        "pending_webhooks": 1,
        "type": "transfer.created"
    }

    def test_webhook_init(self):
        event = Event(kind=None)
        webhook = Webhook(event)
        self.assertIsNone(webhook.name)

    @patch("stripe.Event.retrieve")
    @patch("stripe.Transfer.retrieve")
    def test_webhook_with_transfer_event(self, TransferMock, StripeEventMock):
        StripeEventMock.return_value.to_dict.return_value = self.event_data
        TransferMock.return_value = self.event_data["data"]["object"]
        msg = json.dumps(self.event_data)
        resp = Client().post(
            reverse("pinax_stripe_webhook"),
            msg,
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Event.objects.filter(kind="transfer.created").exists())

    @patch("stripe.Event.retrieve")
    def test_webhook_associated_with_stripe_account(self, StripeEventMock):
        connect_event_data = self.event_data.copy()
        connect_event_data["account"] = "acc_XXX"
        StripeEventMock.return_value.to_dict.return_value = connect_event_data
        msg = json.dumps(connect_event_data)
        resp = Client().post(
            reverse("pinax_stripe_webhook"),
            msg,
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Event.objects.filter(kind="transfer.created").exists())
        self.assertEqual(
            Event.objects.filter(kind="transfer.created").first().account_id,
            "acc_XXX"
        )

    def test_webhook_duplicate_event(self):
        data = {"id": 123}
        Event.objects.create(stripe_id=123, livemode=True, webhook_message={})
        msg = json.dumps(data)
        resp = Client().post(
            reverse("pinax_stripe_webhook"),
            msg,
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Event.objects.filter(stripe_id="123").count(), 1)

    def test_webhook_event_mismatch(self):
        event = Event(kind="account.updated")
        WH = registry.get("account.application.deauthorized")
        with self.assertRaises(Exception):
            WH(event)

    @patch("django.dispatch.Signal.send")
    def test_send_signal(self, SignalSendMock):
        event = Event(kind="account.application.deauthorized")
        WH = registry.get("account.application.deauthorized")
        WH(event).send_signal()
        self.assertTrue(SignalSendMock.called)

    def test_send_signal_not_sent(self):
        event = Event(kind="account.application.deauthorized")
        WH = registry.get("account.application.deauthorized")

        def signal_handler(sender, *args, **kwargs):
            self.fail("Should not have been called.")
        registry.get_signal("account.application.deauthorized").connect(signal_handler)
        webhook = WH(event)
        webhook.name = "mismatch name"  # Not sure how this ever happens due to the registry
        webhook.send_signal()

    @patch("pinax.stripe.webhooks.Webhook.validate")
    @patch("pinax.stripe.webhooks.Webhook.process_webhook")
    def test_process_exception_is_logged(self, ProcessWebhookMock, ValidateMock):
        # note: we choose an event type for which we do no processing
        event = Event.objects.create(kind="account.external_account.created", webhook_message={}, valid=True, processed=False)
        ProcessWebhookMock.side_effect = stripe.error.StripeError("Message", "error")
        with self.assertRaises(stripe.error.StripeError):
            AccountExternalAccountCreatedWebhook(event).process()
        self.assertTrue(EventProcessingException.objects.filter(event=event).exists())

    @patch("pinax.stripe.webhooks.Webhook.validate")
    def test_process_already_processed(self, ValidateMock):
        event = Event.objects.create(kind="account.external_account.created", webhook_message={}, valid=True, processed=True)
        hook = registry.get(event.kind)
        hook(event).process()
        self.assertFalse(ValidateMock.called)

    @patch("pinax.stripe.webhooks.Webhook.validate")
    @patch("pinax.stripe.webhooks.Webhook.process_webhook")
    def test_process_not_valid(self, ProcessWebhookMock, ValidateMock):
        event = Event.objects.create(kind="account.external_account.created", webhook_message={}, valid=False, processed=False)
        hook = registry.get(event.kind)
        hook(event).process()
        self.assertTrue(ValidateMock.called)
        self.assertFalse(ProcessWebhookMock.called)

    @patch("pinax.stripe.webhooks.Webhook.validate")
    @patch("pinax.stripe.webhooks.Webhook.process_webhook")
    def test_process_exception_is_logged_non_stripeerror(self, ProcessWebhookMock, ValidateMock):
        # note: we choose an event type for which we do no processing
        event = Event.objects.create(kind="account.external_account.created", webhook_message={}, valid=True, processed=False)
        ProcessWebhookMock.side_effect = Exception("generic exception")
        with self.assertRaises(Exception):
            AccountExternalAccountCreatedWebhook(event).process()
        self.assertTrue(EventProcessingException.objects.filter(event=event).exists())

    @patch("pinax.stripe.webhooks.Webhook.validate")
    def test_process_return_none(self, ValidateMock):
        # note: we choose an event type for which we do no processing
        event = Event.objects.create(kind="account.external_account.created", webhook_message={}, valid=True, processed=False)
        self.assertIsNone(AccountExternalAccountCreatedWebhook(event).process())

    @patch("stripe.Event.retrieve")
    def test_process_deauthorize(self, RetrieveMock):
        data = {"data": {"object": {"id": "evt_001"}},
                "account": "acct_bb"}
        event = Event.objects.create(
            kind=AccountApplicationDeauthorizeWebhook.name,
            webhook_message=data,
        )
        RetrieveMock.side_effect = stripe.error.PermissionError(
            "The provided key 'sk_test_********************abcd' does not have access to account 'acct_aa' (or that account does not exist). Application access may have been revoked.")
        AccountApplicationDeauthorizeWebhook(event).process()
        self.assertTrue(event.valid)
        self.assertTrue(event.processed)

    @patch("stripe.Event.retrieve")
    def test_process_deauthorize_fake_response(self, RetrieveMock):
        data = {"data": {"object": {"id": "evt_001"}},
                "account": "acct_bb"}
        event = Event.objects.create(
            kind=AccountApplicationDeauthorizeWebhook.name,
            webhook_message=data,
        )
        RetrieveMock.side_effect = stripe.error.PermissionError(
            "The provided key 'sk_test_********************ABCD' does not have access to account 'acc_aa' (or that account does not exist). Application access may have been revoked.")
        with self.assertRaises(stripe.error.PermissionError):
            AccountApplicationDeauthorizeWebhook(event).process()

    @patch("stripe.Event.retrieve")
    def test_process_deauthorize_with_delete_account(self, RetrieveMock):
        data = {"data": {"object": {"id": "evt_002"}},
                "account": "acct_bb"}
        event = Event.objects.create(
            kind=AccountApplicationDeauthorizeWebhook.name,
            webhook_message=data,
        )
        RetrieveMock.side_effect = stripe.error.PermissionError(
            "The provided key 'sk_test_********************abcd' does not have access to account 'acct_bb' (or that account does not exist). Application access may have been revoked.")
        AccountApplicationDeauthorizeWebhook(event).process()
        self.assertTrue(event.valid)
        self.assertTrue(event.processed)

    @patch("stripe.Event.retrieve")
    def test_process_deauthorize_without_account(self, RetrieveMock):
        data = {"data": {"object": {"id": "evt_001"}}}
        event = Event.objects.create(
            kind=AccountApplicationDeauthorizeWebhook.name,
            webhook_message=data,
        )
        RetrieveMock.return_value.to_dict.return_value = data
        AccountApplicationDeauthorizeWebhook(event).process()
        self.assertTrue(event.valid)
        self.assertTrue(event.processed)

    @patch("stripe.Event.retrieve")
    def test_process_deauthorize_without_account_exception(self, RetrieveMock):
        data = {"data": {"object": {"id": "evt_001"}}}
        event = Event.objects.create(
            kind=AccountApplicationDeauthorizeWebhook.name,
            webhook_message=data,
        )
        RetrieveMock.side_effect = stripe.error.PermissionError()
        RetrieveMock.return_value.to_dict.return_value = data
        AccountApplicationDeauthorizeWebhook(event).process()
        self.assertTrue(event.valid)
        self.assertTrue(event.processed)
