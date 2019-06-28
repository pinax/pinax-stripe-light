import stripe

from .. import models, utils


def sync_plans():
    """
    Synchronizes all plans from the Stripe API
    """
    plans = stripe.Plan.auto_paging_iter()
    for plan in plans:
        sync_plan(plan)


def sync_plan(plan, event=None):
    """
    Synchronizes a plan from the Stripe API

    Args:
        plan: data from Stripe API representing a plan
        event: the event associated with the plan
    """

    defaults = {x: plan[x] for x in [
        "currency",
        "interval",
        "interval_count",
        "statement_descriptor",
        "trial_period_days",
        "metadata",
        "active"
    ] if x in plan}

    defaults["amount"] = utils.convert_amount_for_db(plan["amount"], plan["currency"])

    obj, created = models.Plan.objects.get_or_create(
        stripe_id=plan["id"],
        defaults=defaults
    )
    utils.update_with_defaults(obj, defaults, created)
