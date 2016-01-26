import decimal


from django.conf import settings

import stripe

from .. import hooks
from .. import models
from .. import utils


def calculate_refund_amount(charge, amount=None):
    """
    Calculates the refund amount given a charge and optional amount.

    Args:
        charge: a pinax.stripe.models.Charge object
        amount: optionally, the decimal.Decimal amount you wish to refund
    """
    eligible_to_refund = charge.amount - (charge.amount_refunded or 0)
    if amount:
        return min(eligible_to_refund, amount)
    return eligible_to_refund


def capture(charge, amount=None):
    """
    Capture the payment of an existing, uncaptured, charge.

    Args:
        charge: a pinax.stripe.models.Charge object
        amount: the decimal.Decimal amount of the charge to capture
    """
    stripe_charge = charge.stripe_charge.capture(
        amount=utils.convert_amount_for_api(
            amount if amount else charge.amount,
            charge.currency
        )
    )
    sync_charge_from_stripe_data(stripe_charge)


def create(amount, customer, source=None, currency="usd", description=None, send_receipt=settings.PINAX_STRIPE_SEND_EMAIL_RECEIPTS, capture=True):
    """
    Creates a charge for the given customer.

    Args:
        amount: should be a decimal.Decimal amount
        customer: the Stripe id of the customer to charge
        source: the Stripe id of the source belonging to the customer
        currency: the currency with which to charge the amount in
        description: a description of the charge
        send_receipt: send a receipt upon successful charge
        capture: immediately capture the charge instead of doing a pre-authorization

    Returns:
        a pinax.stripe.models.Charge object
    """
    if not isinstance(amount, decimal.Decimal):
        raise ValueError(
            "You must supply a decimal value representing dollars."
        )
    stripe_charge = stripe.Charge.create(
        amount=utils.convert_amount_for_api(amount, currency),  # find the final amount
        currency=currency,
        source=source,
        customer=customer,
        description=description,
        capture=capture,
    )
    charge = sync_charge_from_stripe_data(stripe_charge)
    if send_receipt:
        hooks.hookset.send_receipt(charge)
    return charge


def sync_charges_for_customer(customer):
    """
    Populate database with all the charges for a customer.

    Args:
        customer: a pinax.stripe.models.Customer object
    """
    for charge in customer.stripe_customer.charges().data:
        sync_charge_from_stripe_data(charge)


def sync_charge_from_stripe_data(data):
    """
    Create or update the charge represented by the data from a Stripe API query.

    Args:
        data: the data representing a charge object in the Stripe API

    Returns:
        a pinax.stripe.models.Charge object
    """
    customer = models.Customer.objects.get(stripe_id=data["customer"])
    obj, _ = models.Charge.objects.get_or_create(
        customer=customer,
        stripe_id=data["id"]
    )
    obj.source = data["source"]["id"]
    obj.currency = data["currency"]
    obj.invoice = next(iter(models.Invoice.objects.filter(stripe_id=data["invoice"])), None)
    obj.amount = utils.convert_amount_for_db(data["amount"], obj.currency)
    obj.paid = data["paid"]
    obj.refunded = data["refunded"]
    obj.captured = data["captured"]
    obj.disputed = data["dispute"] is not None
    obj.charge_created = utils.convert_tstamp(data, "created")
    if data.get("description"):
        obj.description = data["description"]
    if data.get("amount_refunded"):
        obj.amount_refunded = utils.convert_amount_for_db(data["amount_refunded"], obj.currency)
    if data["refunded"]:
        obj.amount_refunded = obj.amount
    obj.save()
    return obj
