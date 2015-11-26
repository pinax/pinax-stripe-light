from django.utils import timezone
from django.utils.encoding import smart_str

import stripe

from .. import managers
from .. import models


class CustomerProxy(models.Customer):

    objects = managers.CustomerManager()

    class Meta:
        proxy = True

    @property
    def stripe_customer(self):
        return stripe.Customer.retrieve(self.stripe_id)

    @classmethod
    def get_for_user(cls, user):
        return next(iter(cls.objects.filter(user=user)), None)

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
        self.date_purged = timezone.now()
        self.save()

    def delete(self, using=None):
        # Only way to delete a customer is to use SQL
        self.purge()

    def can_charge(self):
        if self.date_purged is not None:
            return False
        if self.default_source:
            return True
        return False
