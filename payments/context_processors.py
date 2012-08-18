from django.conf import settings

from payments.models import PLAN_CHOICES


def payments_settings(request):
    return {
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
        "PLAN_CHOICES": PLAN_CHOICES,
        "PAYMENT_PLANS": settings.PAYMENTS_PLANS
    }
