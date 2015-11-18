import datetime
import decimal

from django.utils.encoding import smart_str

import stripe

from . import syncs
from ..conf import settings
from .. import hooks
from .. import proxies
from .. import signals
from .. import utils


def get_customer_for_user(user):
    return proxies.CustomerProxy.get_for_user(user)


def charge(customer, amount, currency="usd", description=None, send_receipt=True, capture=True):
    """
    This method expects `amount` to be a Decimal type representing a
    dollar amount. It will be converted to cents so any decimals beyond
    two will be ignored.
    """
    if not isinstance(amount, decimal.Decimal):
        raise ValueError(
            "You must supply a decimal value representing dollars."
        )
    resp = stripe.Charge.create(
        amount=utils.convert_amount_for_api(amount, currency),  # find the final amount
        currency=currency,
        customer=customer.stripe_id,
        description=description,
        capture=capture,
    )
    obj = syncs.sync_charge_from_stripe_data(stripe.Charge.retrieve(resp["id"]))
    if send_receipt:
        obj.send_receipt()
    return obj


def create_customer(user, card=None, plan=None, charge_immediately=True):

    if card and plan:
        plan = settings.PINAX_STRIPE_PLANS[plan]["stripe_plan_id"]
    elif settings.PINAX_STRIPE_DEFAULT_PLAN:
        plan = settings.PINAX_STRIPE_PLANS[settings.PINAX_STRIPE_DEFAULT_PLAN]["stripe_plan_id"]
    else:
        plan = None

    trial_end = hooks.hookset.trial_period(user, plan)

    stripe_customer = stripe.Customer.create(
        email=user.email,
        card=card,
        plan=plan or settings.PINAX_STRIPE_DEFAULT_PLAN,
        trial_end=trial_end
    )

    if stripe_customer.active_card:
        cus = proxies.CustomerProxy.objects.create(
            user=user,
            stripe_id=stripe_customer.id,
            card_fingerprint=stripe_customer.active_card.fingerprint,
            card_last_4=stripe_customer.active_card.last4,
            card_kind=stripe_customer.active_card.type
        )
    else:
        cus = proxies.CustomerProxy.objects.create(
            user=user,
            stripe_id=stripe_customer.id,
        )

    if plan:
        if stripe_customer.subscription:
            syncs.sync_current_subscription_for_customer(cus)
        if charge_immediately:
            cus.send_invoice()

    return cus


def retry_unpaid_invoices(customer):
    syncs.sync_invoices_for_customer(customer)
    for inv in proxies.InvoiceProxy.filter(customer=customer, paid=False, closed=False):
        try:
            inv.retry()  # Always retry unpaid invoices
        except stripe.InvalidRequestError as error:
            if smart_str(error) != "Invoice is already paid":
                raise error


def update_plan_quantity(customer, quantity, charge_immediately=False):
    subscribe(
        customer=customer,
        plan=utils.plan_from_stripe_id(customer.stripe_customer.subscription.plan.id),
        quantity=quantity,
        charge_immediately=charge_immediately
    )


def subscribe(customer, plan, quantity=None, trial_days=None, charge_immediately=True, token=None, coupon=None):
    quantity = hooks.hookset.adjust_subscription_quantity(customer=customer, plan=plan, quantity=quantity)
    cu = customer.stripe_customer

    subscription_params = {}
    if trial_days:
        subscription_params["trial_end"] = datetime.datetime.utcnow() + datetime.timedelta(days=trial_days)
    if token:
        subscription_params["card"] = token

    subscription_params["plan"] = settings.PINAX_STRIPE_PLANS[plan]["stripe_plan_id"]
    subscription_params["quantity"] = quantity
    subscription_params["coupon"] = coupon
    resp = cu.update_subscription(**subscription_params)

    if token:
        # Refetch the stripe customer so we have the updated card info
        cu = customer.stripe_customer
        customer.save_card(cu)

    syncs.sync_current_subscription_for_customer(customer)
    if charge_immediately:
        customer.send_invoice()
    signals.subscription_made.send(sender=customer, plan=plan, stripe_response=resp)
    return resp
