import stripe

from .. import models


class InvoiceProxy(models.Invoice):

    class Meta:
        proxy = True
        ordering = ["-date"]

    @property
    def stripe_invoice(self):
        return stripe.Invoice.retrieve(self.stripe_id)

    def status(self):
        if self.paid:
            return "Paid"
        return "Open"
