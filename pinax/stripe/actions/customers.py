import stripe

from . import syncs
from . import invoices
from ..conf import settings
from .. import hooks
from .. import proxies


def get_customer_for_user(user):
    return proxies.CustomerProxy.get_for_user(user)


def set_default_source(customer, source):
    stripe_customer = customer.stripe_customer
    stripe_customer.default_source = source
    cu = stripe_customer.save()
    syncs.sync_customer(customer, cu=cu)


def create(user, card=None, plan=settings.PINAX_STRIPE_DEFAULT_PLAN, charge_immediately=True):
    trial_end = hooks.hookset.trial_period(user, plan)

    stripe_customer = stripe.Customer.create(
        email=user.email,
        source=card,
        plan=plan,
        trial_end=trial_end
    )
    cus = proxies.CustomerProxy.objects.create(
        user=user,
        stripe_id=stripe_customer["id"]
    )
    syncs.sync_customer(cus, stripe_customer)

    if plan and charge_immediately:
        invoices.create_and_pay(cus)
    return cus
