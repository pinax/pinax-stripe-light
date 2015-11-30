import stripe

from .. import utils
from .. import models


def sync_plans():
    """
    Syncronizes all plans from the Stripe API
    """
    for plan in stripe.Plan.all().data:
        defaults = dict(
            amount=utils.convert_amount_for_db(plan["amount"], plan["currency"]),
            currency=plan["currency"] or "",
            interval=plan["interval"],
            interval_count=plan["interval_count"],
            name=plan["name"],
            statement_descriptor=plan["statement_descriptor"] or "",
            trial_period_days=plan["trial_period_days"]
        )
        obj, created = models.Plan.objects.get_or_create(
            stripe_id=plan["id"],
            defaults=defaults
        )
        utils.update_with_defaults(obj, defaults, created)
