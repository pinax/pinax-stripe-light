import datetime

import stripe
from django.db.models import Q
from django.utils import timezone
from django.utils.encoding import smart_str

from .. import hooks, models, utils


def cancel(subscription, at_period_end=True):
    """
    Cancels a subscription

    Args:
        subscription: the subscription to cancel
        at_period_end: True to cancel at the end of the period, otherwise cancels immediately
    """
    sub = stripe.Subscription(
        subscription.stripe_id,
        stripe_account=subscription.stripe_account_stripe_id,
    ).delete(
        at_period_end=at_period_end,
    )
    return sync_subscription_from_stripe_data(subscription.customer, sub)


def create(customer, plan=None, items=None, quantity=None, trial_days=None, token=None, coupon=None, tax_percent=None, charge_immediately=False, **kwargs):
    """
    Creates a subscription for the given customer

    Args:
        customer: the customer to create the subscription for
        plan: the plan to subscribe to
        items: List of subscription items, each with an attached plan.
        quantity: if provided, the number to subscribe to
        trial_days: if provided, the number of days to trial before starting
        token: if provided, a token from Stripe.js that will be used as the
               payment source for the subscription and set as the default
               source for the customer, otherwise the current default source
               will be used
        coupon: if provided, a coupon to apply towards the subscription
        tax_percent: if provided, add percentage as tax
        charge_immediately: optionally, whether or not to charge immediately
        kwargs: any other parameter you need to pass to the stripe api

    Returns:
        the pinax.stripe.models.Subscription object (created or updated)
    """

    if items and plan:
        ValueError("You can pass either items or plans but not both")

    quantity = hooks.hookset.adjust_subscription_quantity(customer=customer, plan=plan, quantity=quantity)

    subscription_params = {}
    if trial_days:
        subscription_params["trial_end"] = datetime.datetime.utcnow() + datetime.timedelta(days=trial_days)

    if token:
        subscription_params["source"] = token

    if charge_immediately:
        subscription_params["trial_end"] = 'now'

    subscription_params["stripe_account"] = customer.stripe_account_stripe_id
    subscription_params["customer"] = customer.stripe_id
    subscription_params["plan"] = plan
    subscription_params["items"] = items
    subscription_params["quantity"] = quantity
    subscription_params["coupon"] = coupon
    subscription_params["tax_percent"] = tax_percent

    if items:
        del subscription_params['plan']
        del subscription_params['quantity']

    subscription_params.update(kwargs)

    resp = stripe.Subscription.create(**subscription_params)

    return sync_subscription_from_stripe_data(customer, resp)


def has_active_subscription(customer):
    """
    Checks if the given customer has an active subscription

    Args:
        customer: the customer to check

    Returns:
        True, if there is an active subscription, otherwise False
    """
    return models.Subscription.objects.filter(
        customer=customer
    ).filter(
        Q(ended_at__isnull=True) | Q(ended_at__gt=timezone.now())
    ).exists()


def is_period_current(subscription):
    """
    Tests if the provided subscription object for the current period

    Args:
        subscription: a pinax.stripe.models.Subscription object to test
    """
    return subscription.current_period_end > timezone.now()


def is_status_current(subscription):
    """
    Tests if the provided subscription object has a status that means current

    Args:
        subscription: a pinax.stripe.models.Subscription object to test
    """
    return subscription.status in subscription.STATUS_CURRENT


def is_valid(subscription):
    """
    Tests if the provided subscription object is valid

    Args:
        subscription: a pinax.stripe.models.Subscription object to test
    """
    if not is_status_current(subscription):
        return False

    if subscription.cancel_at_period_end and not is_period_current(subscription):
        return False

    return True


def retrieve(customer, sub_id):
    """
    Retrieve a subscription object from Stripe's API

    Args:
        customer: a legacy argument, we check that the given
            subscription belongs to the given customer
        sub_id: the Stripe ID of the subscription you are fetching

    Returns:
        the data for a subscription object from the Stripe API
    """
    if not sub_id:
        return

    try:
        subscription = stripe.Subscription.retrieve(sub_id, stripe_account=customer.stripe_account_stripe_id)
    except stripe.InvalidRequestError as e:
        if smart_str(e).find("No such subscription") >= 0:
            return
        else:
            raise e

    if subscription and subscription.customer != customer.stripe_id:
        return
    return subscription


def sync_subscription_from_stripe_data(customer, subscription):
    """
    Synchronizes data from the Stripe API for a subscription

    Args:
        customer: the customer who's subscription you are syncronizing
        subscription: data from the Stripe API representing a subscription

    Returns:
        the pinax.stripe.models.Subscription object (created or updated)
    """
    from .subscriptionitems import sync_subscription_items

    plan = subscription['plan']
    plan = models.Plan.objects.get(stripe_id=subscription["plan"]["id"]) if plan else None

    defaults = dict(
        customer=customer,
        application_fee_percent=subscription["application_fee_percent"],
        cancel_at_period_end=subscription["cancel_at_period_end"],
        canceled_at=utils.convert_tstamp(subscription["canceled_at"]),
        current_period_start=utils.convert_tstamp(subscription["current_period_start"]),
        current_period_end=utils.convert_tstamp(subscription["current_period_end"]),
        ended_at=utils.convert_tstamp(subscription["ended_at"]),
        plan=plan,
        quantity=subscription["quantity"],
        start=utils.convert_tstamp(subscription["start"]),
        status=subscription["status"],
        trial_start=utils.convert_tstamp(subscription["trial_start"]) if subscription["trial_start"] else None,
        trial_end=utils.convert_tstamp(subscription["trial_end"]) if subscription["trial_end"] else None
    )

    sub, created = models.Subscription.objects.get_or_create(
        stripe_id=subscription["id"],
        defaults=defaults
    )

    pause_collection_instance = None
    pause_collection = subscription["pause_collection"]
    if pause_collection:
        pc_defaults = {
            "behavior": pause_collection.get('behavior'),
            "resumes_at": utils.convert_tstamp(pause_collection.get('resumes_at'))
        }
        if sub.pause_collection:
            pause_collection_instance = utils.update_with_defaults(sub.pause_collection, pc_defaults, False)
        else:
            pause_collection_instance = models.PauseCollection.objects.create(**pc_defaults)
    else:
        try:
            sub.pause_collection.delete()
        except AttributeError:
            pass

    defaults['pause_collection'] = pause_collection_instance

    sub = utils.update_with_defaults(sub, defaults, created)
    sub = sync_subscription_items(sub) or sub
    return sub

def get_subscription_item_by_plan_id(stripe_subscription, plan_id):
    subscription_item = None
    subscription_items = stripe_subscription['items']['data']
    for si in subscription_items:
        stripe_plan_id = si['plan']['id']
        if stripe_plan_id == plan_id:
            subscription_item = si
            break
    return subscription_item

def update_plan(subscription, new_plan, old_plan, prorate=None):

    stripe_subscription = subscription.stripe_subscription
    subscription_item = get_subscription_item_by_plan_id(stripe_subscription, old_plan)

    if not subscription_item:
        raise RuntimeError("old plan does not exist")

    prorate = False if not prorate else prorate

    stripe_subscription_item = subscription_item.stripe_subscription_item
    stripe_subscription_item.plan = new_plan
    stripe_subscription.prorate = prorate
    stripe_subscription_item.save()

def remove_plan(subscription, plan):

    stripe_subscription = subscription.stripe_subscription
    subscription_item = get_subscription_item_by_plan_id(stripe_subscription, plan)
    if subscription_item:
        subscription_item.delete()

def add_plan(subscription, plan, **kwargs):
    from .subscriptionitems import create as create_subscription_item
    stripe_subscription = subscription.stripe_subscription
    subscription_item = get_subscription_item_by_plan_id(stripe_subscription, plan)
    if not subscription_item:
        create_subscription_item(stripe_subscription, plan, **kwargs)

def update(subscription, plan=None, quantity=None, items=None, prorate=True, coupon=None, charge_immediately=False):
    """
    Updates a subscription

    Args:
        subscription: the subscription to update
        plan: optionally, the plan to change the subscription to
        quantity: optionally, the quantity of the subscription to change
        items: optionally, List of subscription items, each with an attached plan.
        prorate: optionally, if the subscription should be prorated or not
        coupon: optionally, a coupon to apply to the subscription
        charge_immediately: optionally, whether or not to charge immediately
    """

    if items and plan:
        ValueError("You can pass either items or plans but not both")

    stripe_subscription = subscription.stripe_subscription

    prorate = False if not prorate else prorate

    if plan:
        stripe_subscription.plan = plan
        stripe_subscription.quantity = quantity

    stripe_subscription.prorate = prorate

    if coupon:
        stripe_subscription.coupon = coupon

    if charge_immediately:
        trial_end = utils.convert_tstamp(stripe_subscription.trial_end)
        if not trial_end or trial_end > timezone.now():
            stripe_subscription.trial_end = 'now'

    sub = stripe_subscription.save()

    if items:
        # sync is done inside the replace_items
        subscription = replace_items(subscription, items)
    else:
        customer = models.Customer.objects.get(pk=subscription.customer.pk)
        subscription = sync_subscription_from_stripe_data(customer, sub)

    return subscription

def replace_items(subscription, items):

    """
    :param subscription: the subscription to update
    :param items: List of subscription items, each with an attached plan.
    :return: a subscription instance
    """

    # Add any new plan
    for i in items:
        add_plan(subscription, i)

    stripe_subscription = subscription.stripe_subscription
    # retrieve the remote subscription

    # remove anything that is not in the items
    subscription_items = stripe_subscription['items']['data']
    for subscription_item in subscription_items:
        si_plan_id = subscription_item['plan']['id']
        if si_plan_id not in items:
            remove_plan(subscription, si_plan_id)

    # Retrieve the subscription
    stripe_subscription = subscription.stripe_subscription
    customer = models.Customer.objects.get(pk=subscription.customer.pk)
    return sync_subscription_from_stripe_data(customer, stripe_subscription)

