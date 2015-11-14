import decimal

from django.core.management.base import BaseCommand

import stripe

from ...conf import settings


class Command(BaseCommand):

    help = "Make sure your Stripe account has the plans"

    def handle(self, *args, **options):
        stripe.api_key = settings.PINAX_STRIPE_SECRET_KEY
        for plan in settings.PINAX_STRIPE_PLANS:
            if settings.PINAX_STRIPE_PLANS[plan].get("stripe_plan_id"):
                price = settings.PINAX_STRIPE_PLANS[plan]["price"]
                if isinstance(price, decimal.Decimal):
                    amount = int(100 * price)
                else:
                    amount = int(100 * decimal.Decimal(str(price)))

                try:
                    plan_name = settings.PINAX_STRIPE_PLANS[plan]["name"]
                    plan_id = settings.PINAX_STRIPE_PLANS[plan].get("stripe_plan_id")

                    stripe.Plan.create(
                        amount=amount,
                        interval=settings.PINAX_STRIPE_PLANS[plan]["interval"],
                        name=plan_name,
                        currency=settings.PINAX_STRIPE_PLANS[plan]["currency"],
                        trial_period_days=settings.PINAX_STRIPE_PLANS[plan].get(
                            "trial_period_days"),
                        id=plan_id
                    )
                    print("Plan created for {0}".format(plan))
                except Exception as e:
                    print("{0} ({1}): {2}".format(plan_name, plan_id, e))
