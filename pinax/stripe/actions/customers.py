import stripe

from . import invoices
from . import sources
from . import subscriptions
from ..conf import settings
from .. import hooks
from .. import proxies
from .. import utils


def create(user, card=None, plan=settings.PINAX_STRIPE_DEFAULT_PLAN, charge_immediately=True):
    """
    Creates a Stripe customer

    Args:
        user: a user object
        card: optionally, the token for a new card
        plan: a plan to subscribe the user to
        charge_immediately: whether or not the user should be immediately
                            charged for the subscription

    Returns:
        the pinax.stripe.proxies.CustomerProxy object that was created
    """
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


def get_customer_for_user(user):
    """
    Get a customer object for a given user

    Args:
        user: a user object

    Returns:
        a pinax.stripe.proxies.CustomerProxy object
    """
    return proxies.CustomerProxy.get_for_user(user)


def set_default_source(customer, source):
    """
    Sets the default payment source for a customer

    Args:
        customer: a CustomerProxy object
        source: the Stripe ID of the payment source
    """
    stripe_customer = customer.stripe_customer
    stripe_customer.default_source = source
    cu = stripe_customer.save()
    sync_customer(customer, cu=cu)


def sync_customer(customer, cu=None):
    """
    Syncronizes a local CustomerProxy object with details from the Stripe API

    Args:
        customer: a CustomerProxy object
        cu: optionally, data from the Stripe API representing the customer
    """
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
