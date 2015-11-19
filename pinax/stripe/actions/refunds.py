import stripe

from .. import signals
from .. import utils


def create(charge, amount=None):
    if amount is None:
        stripe.Refund.create(charge=charge.stripe_id)
    else:
        stripe.Refund.create(
            charge=charge.stripe_id,
            amount=utils.convert_amount_for_api(charge.calculate_refund_amount(amount=amount), charge.currency)
        )
    signals.charge_refunded.send(sender=charge, charge_proxy=charge)
