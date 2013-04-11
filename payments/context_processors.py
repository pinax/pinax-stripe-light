import warnings
warnings.warn("payments.context_processor is deprecated and is no longer "
              "needed. You can safely remove it from the "
              "TEMPLATE_CONTEXT_PROCESSORS setting.", DeprecationWarning)

from payments import settings


def payments_settings(request):
    return {
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
        "PLAN_CHOICES": settings.PLAN_CHOICES,
        "PAYMENT_PLANS": settings.PAYMENTS_PLANS
    }
