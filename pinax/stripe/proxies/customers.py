from django.utils import timezone
from django.utils.encoding import smart_str

import stripe

from .. import managers
from .. import models
from .. import signals
from .. import utils

from .subscriptions import CurrentSubscriptionProxy


class CustomerProxy(models.Customer):

    objects = managers.CustomerManager()

    class Meta:
        proxy = True

    @property
    def stripe_customer(self):
        return stripe.Customer.retrieve(self.stripe_id)

    @classmethod
    def get_for_user(cls, user):
        return cls.objects.get(user=user)

    def current_subscription(self):
        return next(iter(CurrentSubscriptionProxy.objects.filter(customer=self)), None)

    def purge(self):
        try:
            self.stripe_customer.delete()
        except stripe.InvalidRequestError as e:
            if smart_str(e).startswith("No such customer:"):
                # The exception was thrown because the customer was already
                # deleted on the stripe side, ignore the exception
                pass
            else:
                # The exception was raised for another reason, re-raise it
                raise
        self.user = None
        self.card_fingerprint = ""
        self.card_last_4 = ""
        self.card_kind = ""
        self.date_purged = timezone.now()
        self.save()

    def delete(self, using=None):
        # Only way to delete a customer is to use SQL
        self.purge()

    def can_charge(self):
        return self.card_fingerprint and \
            self.card_last_4 and \
            self.card_kind and \
            self.date_purged is None

    def has_active_subscription(self):
        sub = self.current_subscription()
        return sub.is_valid() if sub is not None else False

    def cancel(self, at_period_end=True):
        try:
            current = self.current_subscription()
        except CurrentSubscriptionProxy.DoesNotExist:
            return
        sub = self.stripe_customer.cancel_subscription(
            at_period_end=at_period_end
        )
        current.status = sub.status
        current.cancel_at_period_end = sub.cancel_at_period_end
        current.current_period_end = utils.convert_tstamp(sub, "current_period_end")
        current.save()
        signals.cancelled.send(sender=self, stripe_response=sub)

    def update_card(self, token):
        cu = self.stripe_customer
        cu.card = token
        cu.save()
        self.save_card(cu)

    def save_card(self, cu=None):
        cu = cu or self.stripe_customer
        active_card = cu.active_card
        self.card_fingerprint = active_card.fingerprint
        self.card_last_4 = active_card.last4
        self.card_kind = active_card.type
        self.save()
        signals.card_changed.send(sender=self, stripe_response=cu)

    def send_invoice(self):
        try:
            invoice = stripe.Invoice.create(customer=self.stripe_id)
            if invoice.amount_due > 0:
                invoice.pay()
            return True
        except stripe.InvalidRequestError:
            return False  # There was nothing to invoice
