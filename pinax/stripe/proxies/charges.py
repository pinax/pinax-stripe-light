import stripe

from .. import hooks
from .. import managers
from .. import models
from .. import signals
from .. import utils


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

    def refund(self, amount=None):
        self.stripe_charge.refund(
            amount=utils.convert_amount_for_api(self.calculate_refund_amount(amount=amount), self.currency)
        )
        signals.charge_refunded.send(sender=self, charge_proxy=self)

    def capture(self, amount=None):
        self.captured = True
        self.stripe_charge.capture(
            amount=utils.convert_amount_for_api(self.calculate_refund_amount(amount=amount), self.currency)
        )
        signals.charge_captured.send(sender=self, charge_proxy=self)

    def send_receipt(self):
        hooks.hookset.send_receipt(self)
