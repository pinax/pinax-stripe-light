import stripe

from .. import models, utils


def sync_coupons():
    """
    Synchronizes all coupons from the Stripe API
    """
    coupons = stripe.Coupon.auto_paging_iter()
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
