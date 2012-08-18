from django.conf import settings


INVOICE_FROM_EMAIL = getattr(
    settings,
    "PAYMENTS_INVOICE_FROM_EMAIL",
    "billing@example.com"
)
PAYMENTS_PLANS = getattr(settings, "PAYMENTS_PLANS", {})
PLAN_CHOICES = [
    (key, settings.PAYMENTS_PLANS[key].get("name", key))
    for key in settings.PAYMENTS_PLANS
]


def plan_from_stripe_id(stripe_id):
    for key in PAYMENTS_PLANS.keys():
        if PAYMENTS_PLANS[key].get("stripe_plan_id") == stripe_id:
            return key
