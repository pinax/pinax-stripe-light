import stripe
from django.utils.encoding import smart_str

from .. import utils
from .. import models
from . import charges

def create(customer, items, currency="usd", source=None, shipping=None, coupon=None, metadata=None, pay_immediately=False):
    """
    Creates a product

    Args:
        customer: The customer to use for this order. 
        items: List of Sku instances constituting the order.
        currency: optionally, Three-letter ISO currency code, in lowercase, default to "usd"
        source: optionally, The source you provide must either be a token, like the ones returned by Stripe.js, or a dictionary containing a user's credit card details
        shipping: optionally, Shipping address for the order. Required if any of the SKUs are for products that have shippable set to true.
        coupon: optionally, A coupon code that represents a discount to be applied to this order.
        metadata: optionally, A set of key/value pairs that you can attach to an order object.
        pay_immediately: optionally, send True if you want to charge the invoice right after it is created
    
    Returns:
        the data representing the order object that was created
    """

    items = list(map(lambda sku: sku.convert_to_order_item() if isinstance(sku, models.Sku) else sku, items))

    params = {
        "customer": customer.stripe_id,
        "currency": currency,
        "items": items,
        "shipping": shipping
    }

    if coupon:
        params.update({"coupon": coupon})

    if metadata:
        params.update({"metadata": metadata})

    stripe_order = stripe.Order.create(**params)
    if pay_immediately:
        try:
            stripe_order = pay(stripe_order, source)
        except stripe.InvalidRequestError:
            # we are failing silently here in order
            # to be able to return the order
            pass

    order = sync_order_from_stripe_data(stripe_order)

    return order

def update(order, coupon=None, metadata=None, selected_shipping_method=None, shipping=None, status=None):
    """
    Updates a product

    Args:
        order: the order to update
        coupon: optionally, A coupon code that represents a discount to be applied to this order.
        metadata: optionally, A set of key/value pairs that you can attach to a product object.
        selected_shipping_method: optionally, The shipping method to select for fulfilling this order.
        shipping: optionally, racking information once the order has been fulfilled. (e,g {"carrier": "UPS", "tracking_number": "1212kj21k2"})
        status: optionally, Current order status. One of created, paid, canceled, fulfilled, or returned
    """

    stripe_order = order.stripe_order

    if coupon:
        stripe_order.coupon = coupon
    if metadata:
        stripe_order.metadata = metadata
    if selected_shipping_method:
        stripe_order.selected_shipping_method = selected_shipping_method
    if shipping:
        stripe_order.shipping = shipping
    if status:
        stripe_order.status = status

    stripe_order.save()
    return sync_order_from_stripe_data(stripe_order)

def retrieve(order_id):
    """
    Retrieve a sku object from Stripe's API

    Stripe throws an exception if the order has been deleted that we are
    attempting to sync. In this case we want to just silently ignore that
    exception but pass on any other.

    Args:
        order_id: the Stripe ID of the order you are fetching

    Returns:
        the data for a order object from the Stripe API
    """
    if not order_id:
        return

    try:
        return stripe.Order.retrieve(order_id)
    except stripe.InvalidRequestError as e:
        if smart_str(e).find("No such order") == -1:
            raise
        else:
            # Not Found
            return None

def pay(order, source=None):
    """
    Pays an order
    
    :param order: models.Order instance
    :param source: the source you provide must either be a token, like the ones returned by Stripe.js, or a dictionary containing a user's credit card details 
    :return: stripe api object
    """
    stripe_order = order.stripe_order if hasattr(order, "stripe_order") else order
    params = {}
    if source:
        params.update({"source": source})

    paid_order = stripe_order.pay(**params)
    return sync_order_from_stripe_data(paid_order)


def create_return(order, items=None):
    """
    :param order: the order to be returned 
    :param items: optional, the full or partial order items to be returned, None to return all the items
    :return: the data for a order object from the Stripe API
    """

    return_params = {}
    stripe_order = order.stripe_order

    if items:
        return_params.update({"items": items})

    stripe_order.return_order(**return_params)
    return sync_order_from_stripe_data(stripe_order)

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

        amount = stripe_order["amount"]
        amount_returned = stripe_order["amount_returned"]
        currency = stripe_order["currency"]

        defaults = dict(
            amount=utils.convert_amount_for_db(amount, currency),
            amount_returned=utils.convert_amount_for_db(amount_returned, currency) if amount_returned else None,
            charge=charge,
            currency=currency,
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

    amount = stripe_order["amount"]
    amount_returned = stripe_order["amount_returned"]
    currency = stripe_order["currency"]

    defaults = dict(
        amount=utils.convert_amount_for_db(amount, currency),
        amount_returned=utils.convert_amount_for_db(amount_returned, currency) if amount_returned else None,
        charge=charge,
        currency=currency,
        customer=customer,
        livemode=stripe_order["livemode"],
        metadata = stripe_order["metadata"],
        selected_shipping_method = stripe_order["selected_shipping_method"],
        shipping = stripe_order["shipping"],
        shipping_methods = stripe_order["shipping_methods"],
        status = stripe_order["status"],
        status_transitions = stripe_order["status_transitions"],
        items = stripe_order["items"]
    )

    order, created = models.Order.objects.get_or_create(
        stripe_id=stripe_order["id"],
        defaults=defaults
    )

    order = utils.update_with_defaults(order, defaults, created)
    return order

def sync_orders_from_customer(customer):
    """
    Syncronizes all orders for a customer

    Args:
        customer: the customer for whom to syncronize all invoices
    """

    stripe_customer = customer.stripe_customer
    try:
        orders = stripe.Order.auto_paging_iter(customer=stripe_customer)
    except AttributeError:
        orders = iter(stripe.Order.list(customer=stripe_customer).data)

    for stripe_order in orders:
        sync_order_from_stripe_data(stripe_order)
