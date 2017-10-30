from contextlib import suppress

from django.utils import timezone
from django.utils.encoding import smart_str

import stripe

from . import invoices, sources, subscriptions
from .. import hooks, models, utils
from ..conf import settings


def can_charge(customer):
    """
    Can the given customer create a charge

    Args:
        customer: a pinax.stripe.models.Customer object
    """
    if customer.date_purged is not None:
        return False
    if customer.default_source:
        return True
    return False


def create(user, card=None, plan=settings.PINAX_STRIPE_DEFAULT_PLAN, charge_immediately=True, quantity=None, stripe_account=None):
    """
    Creates a Stripe customer.

    If a customer already exists, the existing customer will be returned.

    Args:
        user: a user object
        card: optionally, the token for a new card
        plan: a plan to subscribe the user to
        charge_immediately: whether or not the user should be immediately
                            charged for the subscription
        quantity: the quantity (multiplier) of the subscription
        stripe_account: An account object. If given, the Customer and User relation will be established for you through UserAccount model.
        Because a single User might have several Customers, one per Account.

    Returns:
        the pinax.stripe.models.Customer object that was created
    """
    def create_stripe_customer():
        trial_end = hooks.hookset.trial_period(user, plan)
        return stripe.Customer.create(
            email=user.email,
            source=card,
            plan=plan,
            quantity=quantity,
            trial_end=trial_end,
            stripe_account=getattr(stripe_account, "stripe_id", None),
        )

    if stripe_account is not None:
        # we want to allow several customers per user, for any stripe account
        try:
            cus = models.UserAccount.objects.get(user=user, account=stripe_account).customer
        except models.UserAccount.DoesNotExist:
            stripe_customer = create_stripe_customer()
            cus = models.Customer.objects.create(
                stripe_id=stripe_customer["id"]
            )
            models.UserAccount.objects.create(
                user=user, account=stripe_account, customer=cus)
            created = True
        else:
            created = False
    else:
        try:
            cus = models.Customer.objects.get(user=user)
        except models.Customer.DoesNotExist:
            stripe_customer = create_stripe_customer()
            cus = models.Customer.objects.create(
                user=user,
                stripe_id=stripe_customer["id"]
            )
            created = True
        else:
            created = False

    if created:
        sync_customer(cus, stripe_customer)
        if plan and charge_immediately:
            invoices.create_and_pay(cus)
    return cus


def get_customer_for_user(user, stripe_account=None):
    """
    Get a customer object for a given user

    Args:
        user: a user object

    Returns:
        a pinax.stripe.models.Customer object
    """
    if stripe_account is not None:
        return user.customers.get(user_account__account=stripe_account)
    with suppress(models.Customer.DoesNotExist):
        return user.customer


def purge_local(customer):
    customer.user = None
    customer.date_purged = timezone.now()
    customer.save()


def purge(customer):
    """
    Deletes the Stripe customer data and purges the linking of the transaction
    data to the Django user.

    Args:
        customer: the pinax.stripe.models.Customer object to purge
    """
    try:
        customer.stripe_customer.delete()
    except stripe.InvalidRequestError as e:
        if "no such customer:" not in smart_str(e).lower():
            # The exception was thrown because the customer was already
            # deleted on the stripe side, ignore the exception
            raise
    purge_local(customer)


def link_customer(event):
    """
    Links a customer referenced in a webhook event message to the event object

    Args:
        event: the pinax.stripe.models.Event object to link
    """
    cus_id = None
    customer_crud_events = [
        "customer.created",
        "customer.updated",
        "customer.deleted"
    ]
    if event.kind in customer_crud_events:
        cus_id = event.message["data"]["object"]["id"]
    else:
        cus_id = event.message["data"]["object"].get("customer", None)

    if cus_id is not None:
        customer = models.Customer.objects.filter(stripe_id=cus_id).first()
        if customer is not None:
            event.customer = customer
            event.save()


def set_default_source(customer, source):
    """
    Sets the default payment source for a customer

    Args:
        customer: a Customer object
        source: the Stripe ID of the payment source
    """
    stripe_customer = customer.stripe_customer
    stripe_customer.default_source = source
    cu = stripe_customer.save()
    sync_customer(customer, cu=cu)


def sync_customer(customer, cu=None):
    """
    Synchronizes a local Customer object with details from the Stripe API

    Args:
        customer: a Customer object
        cu: optionally, data from the Stripe API representing the customer
    """
    if customer.date_purged is not None:
        return

    if cu is None:
        cu = customer.stripe_customer

    if cu.get("deleted", False):
        purge_local(customer)
        return

    customer.account_balance = utils.convert_amount_for_db(cu["account_balance"], cu["currency"])
    customer.currency = cu["currency"] or ""
    customer.delinquent = cu["delinquent"]
    customer.default_source = cu["default_source"] or ""
    customer.save()
    for source in cu["sources"]["data"]:
        sources.sync_payment_source_from_stripe_data(customer, source)
    for subscription in cu["subscriptions"]["data"]:
        subscriptions.sync_subscription_from_stripe_data(customer, subscription)
