import stripe

from . import charges
from .. import utils


def create(charge, amount=None):
    """
    Creates a refund for a particular charge

    Args:
        charge: the charge against which to create the refund
        amount: how much should the refund be, defaults to None, in which case
                the full amount of the charge will be refunded
    """
    if amount is None:
        stripe.Refund.create(charge=charge.stripe_id, stripe_account=charge.stripe_account_stripe_id)
    else:
        stripe.Refund.create(
            charge=charge.stripe_id,
            stripe_account=charge.stripe_account_stripe_id,
            amount=utils.convert_amount_for_api(charges.calculate_refund_amount(charge, amount=amount), charge.currency)
        )
    charges.sync_charge_from_stripe_data(charge.stripe_charge)
