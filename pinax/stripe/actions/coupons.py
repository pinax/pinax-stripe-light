import stripe

from .. import models, utils


def sync_coupons():
    """
    Synchronizes all coupons from the Stripe API
    """
    try:
        coupons = stripe.Coupon.auto_paging_iter()
    except AttributeError:
        coupons = iter(stripe.Coupon.all().data)

    for coupon in coupons:
        defaults = dict(
            amount_off=(
                utils.convert_amount_for_db(coupon["amount_off"], coupon["currency"])
                if coupon["amount_off"]
                else None
            ),
            currency=coupon["currency"] or "",
            duration=coupon["duration"],
            duration_in_months=coupon["duration_in_months"],
            max_redemptions=coupon["max_redemptions"],
            metadata=coupon["metadata"],
            percent_off=coupon["percent_off"],
            redeem_by=utils.convert_tstamp(coupon["redeem_by"]) if coupon["redeem_by"] else None,
            times_redeemed=coupon["times_redeemed"],
            valid=coupon["valid"],
        )
        obj, created = models.Coupon.objects.get_or_create(
            stripe_id=coupon["id"],
            defaults=defaults
        )
        utils.update_with_defaults(obj, defaults, created)

def sync_coupon_from_stripe_data(stripe_coupon):

    """
    Create or update the sku represented by the data from a Stripe API query.

    Args:
        stripe_coupon: the data representing a Coupon object in the Stripe API

    Returns:
        a pinax.stripe.models.Coupon object
    """

    obj, _ = models.Coupon.objects.get_or_create(stripe_id=stripe_coupon["id"])

    currency = stripe_coupon.get("currency") or "usd"
    amount_off = stripe_coupon.get("amount_off") or 0

    obj.amount_off = utils.convert_amount_for_db(amount_off, currency)
    obj.currency = currency
    obj.duration = stripe_coupon.get("duration")
    obj.duration_in_months = stripe_coupon.get("duration_in_months")
    obj.livemode = stripe_coupon.get("livemode")
    obj.max_redemptions = stripe_coupon.get("max_redemptions")
    obj.metadata = stripe_coupon.get("metadata")
    obj.percent_off = stripe_coupon.get("percent_off")
    obj.redeem_by = utils.convert_tstamp(stripe_coupon, "times_redeemed")
    obj.times_redeemed = stripe_coupon.get("times_redeemed")
    obj.valid = stripe_coupon.get("valid")

    obj.save()
    return obj

def create(duration, c_id=None, currency="usd", amount_off=None, duration_in_months=None, max_redemptions=None,
           metadata=None, percent_off=None):

    coupon_params = {
        "duration": duration,
        "currency": currency
    }

    if c_id:
        coupon_params.update({"id": c_id})

    if amount_off:
        coupon_params.update({"amount_off": utils.convert_amount_for_api(amount_off)})

    if duration_in_months:
        coupon_params.update({"duration_in_months": duration_in_months})

    if max_redemptions:
        coupon_params.update({"max_redemptions": max_redemptions})

    if metadata:
        coupon_params.update({"metadata": metadata})

    if percent_off:
        coupon_params.update({"percent_off": percent_off})

    stripe_coupon = stripe.Coupon.create(**coupon_params)
    return sync_coupon_from_stripe_data(stripe_coupon)

def delete(coupon):
    """
    delete a coupon

    Args:
        coupon: the coupon to delete
    """
    stripe_coupon = stripe.Coupon.retrieve(coupon.stripe_id)
    stripe_coupon.delete()
    coupon.delete()