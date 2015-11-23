import decimal

import stripe

from . import syncs
from .. import utils


def create(amount, source=None, customer=None, currency="usd", description=None, send_receipt=True, capture=True):
    """
    This method expects `amount` to be a Decimal type representing a
    dollar amount. It will be converted to cents so any decimals beyond
    two will be ignored.
    """
    if not isinstance(amount, decimal.Decimal):
        raise ValueError(
            "You must supply a decimal value representing dollars."
        )
    if source is None and customer is None:
        raise ValueError(
            "You must supply either a source or customer to create the charge for"
        )
    stripe_charge = stripe.Charge.create(
        amount=utils.convert_amount_for_api(amount, currency),  # find the final amount
        currency=currency,
        source=source,
        description=description,
        capture=capture,
    )
    charge = syncs.sync_charge_from_stripe_data(stripe_charge)
    if send_receipt:
        charge.send_receipt()
    return charge


def capture(charge, amount):
    stripe_charge = charge.stripe_charge.capture(
        amount=utils.convert_amount_for_api(
            amount,
            charge.currency
        )
    )
    syncs.sync_charge_from_stripe_data(stripe_charge)
