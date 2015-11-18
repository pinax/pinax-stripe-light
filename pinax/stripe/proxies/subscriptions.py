from django.conf import settings
from django.utils import timezone

from .. import models


class CurrentSubscriptionProxy(models.CurrentSubscription):

    class Meta:
        proxy = True

    @property
    def total_amount(self):
        return self.amount * self.quantity

    def plan_display(self):
        return settings.PINAX_STRIPE_PLANS[self.plan]["name"]

    def status_display(self):
        return self.status.replace("_", " ").title()

    def is_period_current(self):
        return self.current_period_end > timezone.now()

    def is_status_current(self):
        return self.status in ["trialing", "active"]

    def is_valid(self):
        if not self.is_status_current():
            return False

        if self.cancel_at_period_end and not self.is_period_current():
            return False

        return True

    def delete(self, using=None):
        """
        Set values to None while deleting the object so that any lingering
        references will not show previous values (such as when an Event
        signal is triggered after a subscription has been deleted)
        """
        super(CurrentSubscriptionProxy, self).delete(using=using)
        self.plan = None
        self.status = None
        self.quantity = 0
        self.amount = 0
