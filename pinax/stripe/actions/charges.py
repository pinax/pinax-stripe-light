import decimal

import stripe

from .. import proxies
from .. import utils


def create(amount, customer, source=None, currency="usd", description=None, send_receipt=True, capture=True):
    """
    This method expects `amount` to be a Decimal type representing a
    dollar amount. It will be converted to cents so any decimals beyond
    two will be ignored.
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
        charge.send_receipt()
    return charge


def capture(charge, amount=None):
    stripe_charge = charge.stripe_charge.capture(
        amount=utils.convert_amount_for_api(
            amount if amount else charge.amount,
            charge.currency
        )
    )
    sync_charge_from_stripe_data(stripe_charge)


def sync_charges_for_customer(customer):
    for charge in customer.stripe_customer.charges().data:
        sync_charge_from_stripe_data(charge)


def sync_charge_from_stripe_data(data):
    customer = proxies.CustomerProxy.objects.get(stripe_id=data["customer"])
    obj, _ = proxies.ChargeProxy.objects.get_or_create(
        customer=customer,
        stripe_id=data["id"]
    )
    obj.source = data["source"]["id"]
    obj.currency = data["currency"]
    obj.invoice = next(iter(proxies.InvoiceProxy.objects.filter(stripe_id=data["invoice"])), None)
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
