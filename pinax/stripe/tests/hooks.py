from datetime import timedelta

from django.utils import timezone

from ..hooks import DefaultHookSet


class TestHookSet(DefaultHookSet):

    def adjust_subscription_quantity(self, customer, plan, quantity):
        """
        Given a customer, plan, and quantity, when calling Customer.subscribe
        you have the opportunity to override the quantity that was specified.

        Previously this was handled in the setting `PAYMENTS_PLAN_QUANTITY_CALLBACK`
        and was only passed a customer object.
        """
        return quantity or 4

    def trial_period(self, user, plan):
        """
        Given a user and plan, return an end date for a trial period, or None
        for no trial period.

        Was previously in the setting `TRIAL_PERIOD_FOR_USER_CALLBACK`
        """
        if plan is not None:
            return timezone.now() + timedelta(days=3)
