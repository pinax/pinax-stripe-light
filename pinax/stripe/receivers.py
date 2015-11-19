from django.dispatch import receiver

import stripe

from .actions import syncs
from .conf import settings
from .signals import charge_refunded, charge_captured, invoice_event_received, customer_subscription_event, charge_event_received


@receiver([charge_refunded, charge_captured])
def handle_charge_actions(sender, *args, **kwargs):
    syncs.sync_charge_from_stripe_data(kwargs["charge_proxy"].stripe_charge)


@receiver(invoice_event_received)
def handle_invoice_event_received(sender, *args, **kwargs):
    event = kwargs.get("event")
    if event.kind.startswith("invoice."):
        syncs.fetch_and_sync_invoice(event.message["data"]["object"]["id"], send_receipt=settings.PINAX_STRIPE_SEND_EMAIL_RECEIPTS)


@receiver(customer_subscription_event)
def handle_customer_subscription_event(sender, *args, **kwargs):
    customer = kwargs.get("customer")
    syncs.sync_customer(customer, customer.stripe_customer)


@receiver(charge_event_received)
def handle_charge_event_received(sender, *args, **kwargs):
    event = kwargs.get("event")
    syncs.sync_charge_from_stripe_data(stripe.Charge.retrieve(event.message["data"]["objects"]["id"]))
