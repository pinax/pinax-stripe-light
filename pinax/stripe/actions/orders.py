import stripe

from .. import utils
from .. import models
from . import charges

def create(customer, items, currency="usd", source=None, shipping=None, coupon=None, metadata=None):

    params = {
        "customer": customer.stripe_id,
        "currency": currency,
        "items": items,
        "shipping": shipping
    }

    if coupon:
        params.update({"coupon": coupon})

    if metadata:
        params.update({"metadata": coupon})

    stripe_order = stripe.Order.create(**params)
    if source:
        stripe_order.pay(source=source)

    order = sync_order_from_stripe_data(stripe_order)

    return order

def sync_orders():
    """
    Synchronizes all the orders from the Stripe API
    """

    try:
        orders = stripe.Order.auto_paging_iter()
    except AttributeError:
        orders = iter(stripe.Order.list().data)

    for stripe_order in orders:
        customer = models.Customer.objects.get(stripe_id=stripe_order["customer"])

        if stripe_order.get("charge"):
            charge = charges.sync_charge_from_stripe_data(stripe.Charge.retrieve(stripe_order["charge"]))
        else:
            charge = None

        defaults = dict(
            amount=utils.convert_amount_for_db(stripe_order["amount"], stripe_order["currency"]),
            amount_returned=utils.convert_amount_for_db(stripe_order["amount_returned"], stripe_order["currency"]),
            charge=charge,
            currency=stripe_order["attributes"],
            customer=customer,
            livemode=stripe_order["livemode"],
            metadata=stripe_order["metadata"],
            selected_shipping_method=stripe_order["selected_shipping_method"],
            shipping=stripe_order["shipping"],
            shipping_methods=stripe_order["shipping_methods"],
            status=stripe_order["status"],
            status_transitions=stripe_order["status_transitions"],
            items=stripe_order["items"]
        )

        obj, created = models.Order.objects.get_or_create(
            stripe_id=stripe_order["id"],
            defaults=defaults
        )
        utils.update_with_defaults(obj, defaults, created)

def sync_order_from_stripe_data(stripe_order):
    """
    Create or update the order represented by the data from a Stripe API query.

    Args:
        stripe_order: the data representing an order object in the Stripe API

    Returns:
        a pinax.stripe.models.Order object
    """

    customer = models.Customer.objects.get(stripe_id=stripe_order["customer"])

    if stripe_order.get("charge"):
        charge = charges.sync_charge_from_stripe_data(stripe.Charge.retrieve(stripe_order["charge"]))
    else:
        charge = None

    obj, _ = models.Order.objects.get_or_create(stripe_id=stripe_order["id"])
    obj.amount = utils.convert_amount_for_db(stripe_order["amount"], stripe_order["currency"]),
    obj.amount_returned = utils.convert_amount_for_db(stripe_order["amount_returned"], stripe_order["currency"]),
    obj.charge = charge,
    obj.currency = stripe_order["attributes"],
    obj.customer = customer,
    obj.livemode = stripe_order["livemode"],
    obj.metadata = stripe_order["metadata"],
    obj.selected_shipping_method = stripe_order["selected_shipping_method"],
    obj.shipping = stripe_order["shipping"],
    obj.shipping_methods = stripe_order["shipping_methods"],
    obj.status = stripe_order["status"],
    obj.status_transitions = stripe_order["status_transitions"],
    obj.items = stripe_order["items"]

    obj.save()
    return obj

def sync_orders_from_customer(customer):
    pass