import logging

from django.utils import timezone
from django.utils.encoding import smart_str

import stripe

from . import invoices, sources, subscriptions
from .. import hooks, models, utils
from ..conf import settings

logger = logging.getLogger(__name__)


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


def _create_without_account(user, card=None, plan=settings.PINAX_STRIPE_DEFAULT_PLAN, charge_immediately=True, quantity=None):
    cus = models.Customer.objects.filter(user=user).first()
    if cus is not None:
        try:
            stripe.Customer.retrieve(cus.stripe_id)
            return cus
        except stripe.error.InvalidRequestError:
            pass

    # At this point we maybe have a local Customer but no stripe customer
    # let's create one and make the binding
    trial_end = hooks.hookset.trial_period(user, plan)
    stripe_customer = stripe.Customer.create(
        email=user.email,
        source=card,
        plan=plan,
        quantity=quantity,
        trial_end=trial_end
    )
    cus, created = models.Customer.objects.get_or_create(
        user=user,
        defaults={
            "stripe_id": stripe_customer["id"]
        }
    )
    if not created:
        cus.stripe_id = stripe_customer["id"]  # sync_customer will call cus.save()
    sync_customer(cus, stripe_customer)
    if plan and charge_immediately:
        invoices.create_and_pay(cus)
    return cus


def _create_with_account(user, stripe_account, card=None, plan=settings.PINAX_STRIPE_DEFAULT_PLAN, charge_immediately=True, quantity=None):
    cus = user.customers.filter(user_account__account=stripe_account).first()
    if cus is not None:
        try:
            stripe.Customer.retrieve(cus.stripe_id, stripe_account=stripe_account.stripe_id)
            return cus
        except stripe.error.InvalidRequestError:
            pass

    # At this point we maybe have a local Customer but no stripe customer
    # let's create one and make the binding
    trial_end = hooks.hookset.trial_period(user, plan)
    stripe_customer = stripe.Customer.create(
        email=user.email,
        source=card,
        plan=plan,
        quantity=quantity,
        trial_end=trial_end,
        stripe_account=stripe_account.stripe_id,
    )

    if cus is None:
        cus = models.Customer.objects.create(stripe_id=stripe_customer["id"], stripe_account=stripe_account)
        models.UserAccount.objects.create(user=user, account=stripe_account, customer=cus)
    else:
        logger.debug("Update local customer %s with new remote customer %s for user %s, and account %s",
                     cus.stripe_id, stripe_customer["id"], user, stripe_account)
        cus.stripe_id = stripe_customer["id"]  # sync_customer() will call cus.save()
    sync_customer(cus, stripe_customer)
    if plan and charge_immediately:
        invoices.create_and_pay(cus)
    return cus


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
        stripe_account: An account object. If given, the Customer and User relation will be established for you through the UserAccount model.
        Because a single User might have several Customers, one per Account.

    Returns:
        the pinax.stripe.models.Customer object that was created
    """
    if stripe_account is None:
        return _create_without_account(user, card=card, plan=plan, charge_immediately=charge_immediately, quantity=quantity)
    return _create_with_account(user, stripe_account, card=card, plan=plan, charge_immediately=charge_immediately, quantity=quantity)


def get_customer_for_user(user, stripe_account=None):
    """
    Get a customer object for a given user

    Args:
         user: a user object
         stripe_account: An Account object

    Returns:
        a pinax.stripe.models.Customer object
    """
    if stripe_account is None:
        return models.Customer.objects.filter(user=user).first()
    return user.customers.filter(user_account__account=stripe_account).first()


def purge_local(customer):
    customer.user_accounts.all().delete()
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
    except stripe.error.InvalidRequestError as e:
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
    event_data_object = event.message["data"]["object"]
    if event.kind in customer_crud_events:
        cus_id = event_data_object["id"]
    else:
        cus_id = event_data_object.get("customer", None)

    if cus_id is not None:
        customer, created = models.Customer.objects.get_or_create(
            stripe_id=cus_id,
            stripe_account=event.stripe_account,
        )
        if event.kind in customer_crud_events:
            sync_customer(customer, event_data_object)

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
