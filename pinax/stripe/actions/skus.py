import stripe
from django.utils.encoding import smart_str

from .. import models
from .. import utils


def create(product, price, inventory, s_id=None, currency="usd", attributes=None, image=None, metadata=None, package_dimensions=None, active=True):
    """
    Creates a sku

    Args:
        product: The product this SKU is associated with.
        price: The cost of the item as a non-negative integer in the smallest currency unit 
        inventory: Description of the SKU’s inventory. e.g
        {
            "quantity": 1,
            "type": "finite", # Possible values are finite, bucket (not quantified), and infinite.
            "value": "limited" # Possible values are in_stock, limited, and out_of_stock
        }
        s_id: optionally, The identifier for the SKU. Must be unique. If not provided, an identifier will be randomly generated.
        currency: optionally, Three-letter ISO currency code, in lowercase. Must be a supported . Defaults to usd
        attributes: optionally, A dictionary of attributes and values for the attributes defined by the product. (e.g {"size": "Medium", "gender": "Unisex"})
        image: optionally, The URL of an image for this SKU, meant to be displayable to the customer.
        metadata: optionally, A set of key/value pairs that you can attach to a product object. It can be useful for storing additional information about the product in a structured format.
        package_dimensions: optionally, The dimensions of this product for shipping purposes, all values are required. e.g
        {
            "height": 20
            "length": 21
            "weight": 22
            "width": 23
        }
        active: optionally, Whether or not the SKU is available for purchase. Default to true

    Returns:
        the data representing the subscription object that was created
    """

    sku_params = {
        "product": product.stripe_id,
        "price": utils.convert_amount_for_api(price, currency=currency),
        "inventory": inventory,
        "currency": currency
    }

    if s_id:
        sku_params.update({"id": s_id})

    if attributes:
        sku_params.update({"attributes": attributes})

    if image:
        sku_params.update({"image": image})

    if metadata:
        sku_params.update({"metadata": metadata})

    if package_dimensions:
        sku_params.update({"package_dimensions": package_dimensions})

    if active:
        sku_params.update({"active": active})

    stripe_sku = stripe.SKU.create(**sku_params)
    return sync_sku_from_stripe_data(stripe_sku)

def update(sku, active=None, attributes=None, currency=None, image=None, inventory=None, metadata=None, package_dimensions=None, price=None, product=None):
    """
    Updates a product

    Args:
        active: optionally, Whether or not this SKU is available for purchase.
        attributes: optionally, A dictionary of attributes and values for the attributes defined by the product.
        currency: optionally, Three-letter ISO currency code, in lowercase. Must be a supported currency.
        image: optionally, The URL of an image for this SKU, meant to be displayable to the customer. 
        inventory: optionally, Description of the SKU’s inventory.
        metadata: optionally, A set of key/value pairs that you can attach to a SKU object.
        package_dimensions: optionally, The dimensions of this SKU for shipping purposes.
        price: optionally, The cost of the item as a positive integer.
        product: optionally, The ID of the product that this SKU should belong to.
    """

    stripe_sku = sku.stripe_sku

    if active is not None:
        stripe_sku.active = active
    if attributes:
        stripe_sku.attributes = attributes
    if currency:
        stripe_sku.currency = currency
    if image:
        stripe_sku.image = image
    if inventory:
        stripe_sku.inventory = inventory
    if metadata:
        stripe_sku.metadata = metadata
    if package_dimensions:
        stripe_sku.package_dimensions = package_dimensions
    if price:
        stripe_sku.price = price
    if product:
        stripe_sku.product = product

    stripe_sku.save()
    return sync_sku_from_stripe_data(stripe_sku)

def delete(sku):
    """
    delete a sku

    Args:
        sku: the sku to delete
    """
    stripe_sku = stripe.Product.retrieve(sku.stripe_id)
    stripe_sku.delete()
    sku.delete()

def retrieve(sku_id):
    """
    Retrieve a sku object from Stripe's API

    Stripe throws an exception if a sku has been deleted that we are
    attempting to sync. In this case we want to just silently ignore that
    exception but pass on any other.

    Args:
        sku_id: the Stripe ID of the sku you are fetching

    Returns:
        the data for a sku object from the Stripe API
    """

    if not sku_id:
        return

    try:
        return stripe.SKU.retrieve(sku_id)
    except stripe.InvalidRequestError as e:
        if smart_str(e).find("No such sku") == -1:
            raise
        else:
            # Not Found
            return None

def sync_skus():
    """
    Synchronizes all the Skus from the Stripe API
    """

    try:
        skus = stripe.SKU.auto_paging_iter()
    except AttributeError:
        skus = iter(stripe.SKU.list().data)

    for stripe_sku in skus:
        product = models.Product.objects.get(stripe_id=stripe_sku["product"])

        defaults = dict(
            product=product,
            price=utils.convert_amount_for_db(stripe_sku["price"], stripe_sku["currency"]),
            currency=stripe_sku["currency"],
            attributes=stripe_sku["attributes"],
            image=stripe_sku["image"],
            inventory=stripe_sku["inventory"],
            livemode=stripe_sku["livemode"],
            metadata=stripe_sku["metadata"],
            package_dimensions=stripe_sku["package_dimensions"],
            active=stripe_sku["active"],
            updated=utils.convert_tstamp(stripe_sku, "updated")
        )

        obj, created = models.Sku.objects.get_or_create(
            stripe_id=stripe_sku["id"],
            defaults=defaults
        )
        utils.update_with_defaults(obj, defaults, created)

def sync_sku_from_stripe_data(stripe_sku):
    """
    Create or update the sku represented by the data from a Stripe API query.

    Args:
        stripe_sku: the data representing a sku object in the Stripe API

    Returns:
        a pinax.stripe.models.Sku object
    """

    product = models.Product.objects.get(stripe_id=stripe_sku["product"])
    obj, _ = models.Sku.objects.get_or_create(stripe_id=stripe_sku["id"])

    obj.product = product
    obj.price = utils.convert_amount_for_db(stripe_sku["price"], stripe_sku["currency"])
    obj.currency = stripe_sku["currency"]
    obj.attributes = stripe_sku["attributes"]
    obj.image = stripe_sku["image"]
    obj.inventory = stripe_sku["inventory"]
    obj.livemode = stripe_sku["livemode"]
    obj.metadata = stripe_sku["metadata"]
    obj.package_dimensions = stripe_sku["package_dimensions"]
    obj.active = stripe_sku["active"]
    obj.updated = utils.convert_tstamp(stripe_sku, "updated")

    obj.save()
    return obj

def sync_skus_from_product(product):
    """
    Populate database with all the skus for a product.

    Args:
        product: a pinax.stripe.models.Product object
    """
    for sku in iter(product.stripe_product.skus.list().data):
        sync_sku_from_stripe_data(sku)
