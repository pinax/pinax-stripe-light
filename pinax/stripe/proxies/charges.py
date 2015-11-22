import stripe

from .. import hooks
from .. import managers
from .. import models


class ChargeProxy(models.Charge):

    objects = managers.ChargeManager()

    class Meta:
        proxy = True

    @property
    def stripe_charge(self):
        return stripe.Charge.retrieve(self.stripe_id)

    def calculate_refund_amount(self, amount=None):
        eligible_to_refund = self.amount - (self.amount_refunded or 0)
        if amount:
            return min(eligible_to_refund, amount)
        return eligible_to_refund

    def send_receipt(self):
        hooks.hookset.send_receipt(self)
