class DefaultHookSet(object):

    def adjust_subscription_quantity(self, customer, plan, quantity):
        """
        Given a customer, plan, and quantity, when calling Customer.subscribe
        you have the opportunity to override the quantity that was specified.

        Previously this was handled in the setting `PAYMENTS_PLAN_QUANTITY_CALLBACK`
        and was only passed a customer object.
        """
        if quantity is None:
            quantity = 1
        return quantity

    def trial_period(self, user, plan):
        """
        Given a user and plan, return an end date for a trial period, or None
        for no trial period.

        Was previously in the setting `TRIAL_PERIOD_FOR_USER_CALLBACK`
        """
        return None


class HookProxy(object):

    def __getattr__(self, attr):
        from .conf import settings  # if put globally there is a race condition
        return getattr(settings.PINAX_STRIPE_HOOKSET, attr)


hookset = HookProxy()
