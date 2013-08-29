from django.conf import settings

from .utils import load_path_attr


STRIPE_PUBLIC_KEY = settings.STRIPE_PUBLIC_KEY
INVOICE_FROM_EMAIL = getattr(
    settings,
    "PAYMENTS_INVOICE_FROM_EMAIL",
    "billing@example.com"
)
PAYMENTS_PLANS = getattr(settings, "PAYMENTS_PLANS", {})
PLAN_CHOICES = [
    (plan, PAYMENTS_PLANS[plan].get("name", plan))
    for plan in PAYMENTS_PLANS
]
DEFAULT_PLAN = getattr(
    settings,
    "PAYMENTS_DEFAULT_PLAN",
    None
)
TRIAL_PERIOD_FOR_USER_CALLBACK = getattr(
    settings,
    "PAYMENTS_TRIAL_PERIOD_FOR_USER_CALLBACK",
    None
)
PLAN_QUANTITY_CALLBACK = getattr(
    settings,
    "PAYMENTS_PLAN_QUANTITY_CALLBACK",
    None
)

if isinstance(TRIAL_PERIOD_FOR_USER_CALLBACK, basestring):
    TRIAL_PERIOD_FOR_USER_CALLBACK = load_path_attr(
        TRIAL_PERIOD_FOR_USER_CALLBACK
    )

if isinstance(PLAN_QUANTITY_CALLBACK, basestring):
    PLAN_QUANTITY_CALLBACK = load_path_attr(PLAN_QUANTITY_CALLBACK)

SEND_EMAIL_RECEIPTS = getattr(settings, "SEND_EMAIL_RECEIPTS", True)


def plan_from_stripe_id(stripe_id):
    for key in PAYMENTS_PLANS.keys():
        if PAYMENTS_PLANS[key].get("stripe_plan_id") == stripe_id:
            return key
