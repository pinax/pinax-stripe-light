from django.conf import settings
from django.core.management.base import BaseCommand

import stripe


class Command(BaseCommand):
    
    help = "Make sure your Stripe account has the plans"
    
    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        for plan in settings.PAYMENTS_PLANS:
            if settings.PAYMENTS_PLANS[plan].get("stripe_plan_id"):
                stripe.Plan.create(
                    amount=100 * settings.PAYMENTS_PLANS[plan]["price"],
                    interval=settings.PAYMENTS_PLANS[plan]["interval"],
                    name=settings.PAYMENTS_PLANS[plan]["name"],
                    currency="usd",
                    id=settings.PAYMENTS_PLANS[plan].get("stripe_plan_id")
                )
                print "Plan created for %s" % plan
