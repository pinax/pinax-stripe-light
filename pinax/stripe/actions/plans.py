import stripe

from .. import utils
from .. import models


def sync_plans():
    """
    Syncronizes all plans from the Stripe API
    """
    try:
        plans = stripe.Plan.auto_paging_iter()
    except AttributeError:
        plans = iter(stripe.Plan.all().data)

    for plan in plans:
        defaults = dict(
            amount=utils.convert_amount_for_db(plan["amount"], plan["currency"]),
            currency=plan["currency"] or "",
            interval=plan["interval"],
            interval_count=plan["interval_count"],
            name=plan["name"],
            statement_descriptor=plan["statement_descriptor"] or "",
            trial_period_days=plan["trial_period_days"],
            metadata=plan["metadata"]
        )
        obj, created = models.Plan.objects.get_or_create(
            stripe_id=plan["id"],
            defaults=defaults
        )
        utils.update_with_defaults(obj, defaults, created)
