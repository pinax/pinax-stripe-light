import datetime

from . import syncs
from ..conf import settings
from .. import hooks
from .. import proxies


def current_subscription(customer):
    # @@@ hack until views are rewritten
    return next(iter(proxies.SubscriptionProxy.objects.filter(customer=customer)), None)


def delete(stripe_id):
    sub = next(iter(proxies.SubscriptionProxy.objects.filter(stripe_id=stripe_id)), None)
    if sub is not None:
        sub.delete()


def cancel(subscription, at_period_end=True):
    sub = subscription.stripe_subscription.delete(at_period_end=at_period_end)
    syncs.sync_subscription_from_stripe_data(sub)


def update(subscription, plan=None, quantity=None, prorate=True, coupon=None, charge_immediately=False):
    stripe_subscription = subscription.stripe_subscription
    if plan:
        stripe_subscription.plan = plan
    if quantity:
        stripe_subscription.quantity = quantity
    if not prorate:
        stripe_subscription.prorate = False
    if coupon:
        stripe_subscription.coupon = coupon
    sub = stripe_subscription.save()
    customer = proxies.CustomerProxy.objects.get(pk=subscription.customer.pk)
    syncs.sync_subscription_from_stripe_data(customer, sub)


def create(customer, plan, quantity=None, trial_days=None, charge_immediately=True, token=None, coupon=None):
    quantity = hooks.hookset.adjust_subscription_quantity(customer=customer, plan=plan, quantity=quantity)
    cu = customer.stripe_customer

    subscription_params = {}
    if trial_days:
        subscription_params["trial_end"] = datetime.datetime.utcnow() + datetime.timedelta(days=trial_days)
    if token:
        subscription_params["source"] = token

    subscription_params["plan"] = plan
    subscription_params["quantity"] = quantity
    subscription_params["coupon"] = coupon
    resp = cu.subscriptions.create(**subscription_params)

    if charge_immediately:
        customer.send_invoice()
    return resp
