import stripe

from .. import models, utils


def sync_coupons():
    """
    Synchronizes all coupons from the Stripe API

    TODO: Support connect / stripe_account param
    """
    coupons = stripe.Coupon.auto_paging_iter()
    for coupon in coupons:
        sync_coupon_from_stripe_data(coupon)


def sync_coupon_from_stripe_data(coupon, stripe_account=None):
        defaults = dict(
            amount_off=(
                utils.convert_amount_for_db(coupon["amount_off"], coupon["currency"])
                if coupon["amount_off"]
                else None
            ),
            currency=coupon["currency"] or "",
            duration=coupon["duration"],
            duration_in_months=coupon["duration_in_months"],
            livemode=coupon["livemode"],
            max_redemptions=coupon["max_redemptions"],
            metadata=coupon["metadata"],
            percent_off=coupon["percent_off"],
            redeem_by=utils.convert_tstamp(coupon["redeem_by"]) if coupon["redeem_by"] else None,
            times_redeemed=coupon["times_redeemed"],
            valid=coupon["valid"],
            stripe_account=stripe_account,
        )
        obj, created = models.Coupon.objects.get_or_create(
            stripe_id=coupon["id"],
            stripe_account=stripe_account,
            defaults=defaults
        )
        utils.update_with_defaults(obj, defaults, created)
        return obj


def purge_local(coupon, stripe_account=None):
    return models.Coupon.objects.filter(
        stripe_id=coupon["id"], stripe_account=stripe_account).delete()
