import stripe

from . import invoices
from . import sources
from . import subscriptions
from ..conf import settings
from .. import hooks
from .. import proxies
from .. import utils


def get_customer_for_user(user):
    return proxies.CustomerProxy.get_for_user(user)


def set_default_source(customer, source):
    stripe_customer = customer.stripe_customer
    stripe_customer.default_source = source
    cu = stripe_customer.save()
    sync_customer(customer, cu=cu)


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
    sync_customer(cus, stripe_customer)

    if plan and charge_immediately:
        invoices.create_and_pay(cus)
    return cus


def sync_customer(customer, cu=None):
    if cu is None:
        cu = customer.stripe_customer
    customer.account_balance = utils.convert_amount_for_db(cu["account_balance"], cu["currency"])
    customer.currency = cu["currency"] or ""
    customer.delinquent = cu["delinquent"]
    customer.default_source = cu["default_source"] or ""
    customer.save()
    for source in cu["sources"]["data"]:
        sources.sync_payment_source_from_stripe_data(customer, source)
    for subscription in cu["subscriptions"]["data"]:
        subscriptions.sync_subscription_from_stripe_data(customer, subscription)
