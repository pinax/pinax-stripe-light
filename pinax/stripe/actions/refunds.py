import stripe

from . import charges
from .. import utils


def create(charge, amount=None):
    if amount is None:
        stripe.Refund.create(charge=charge.stripe_id)
    else:
        stripe.Refund.create(
            charge=charge.stripe_id,
            amount=utils.convert_amount_for_api(charge.calculate_refund_amount(amount=amount), charge.currency)
        )
    charges.sync_charge_from_stripe_data(charge.stripe_charge)
