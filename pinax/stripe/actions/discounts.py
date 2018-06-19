from .. import models, utils
from .coupons import sync_coupon_from_stripe_data


def sync_discounts_from_stripe_data(stripe_discount, customer=None):

    customer_stripe_id = stripe_discount.get('customer')
    if not customer:
        customer = models.Customer.objects.get(stripe_id=customer_stripe_id)

    if customer.stripe_id != customer_stripe_id:
        raise ValueError("The customer must match the discount customer")

    stripe_coupon = stripe_discount.get('coupon')
    coupon = sync_coupon_from_stripe_data(stripe_coupon)

    obj, _ = models.Discount.objects.get_or_create(customer=customer, coupon=coupon)

    obj.start = utils.convert_tstamp(stripe_discount["start"])
    obj.end = utils.convert_tstamp(stripe_discount["end"])
    obj.save()

    return obj






