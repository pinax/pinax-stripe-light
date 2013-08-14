from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import importlib


def get_user_model():
    try:
        # pylint: disable-msg=E0611
        from django.contrib.auth import get_user_model as django_get_user_model
        return django_get_user_model()
    except ImportError:
        from django.contrib.auth.models import User
        return User


def plan_from_stripe_id(stripe_id):
    for key in PAYMENTS_PLANS.keys():
        if PAYMENTS_PLANS[key].get("stripe_plan_id") == stripe_id:
            return key


def load_path_attr(path):
    i = path.rfind(".")
    module, attr = path[:i], path[i + 1:]
    try:
        mod = importlib.import_module(module)
    except ImportError, e:
        raise ImproperlyConfigured("Error importing %s: '%s'" % (module, e))
    try:
        attr = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured("Module '%s' does not define a '%s'" % (
            module, attr)
        )
    return attr


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
if isinstance(TRIAL_PERIOD_FOR_USER_CALLBACK, basestring):
    TRIAL_PERIOD_FOR_USER_CALLBACK = load_path_attr(
        TRIAL_PERIOD_FOR_USER_CALLBACK
    )
SEND_EMAIL_RECEIPTS = getattr(settings, "SEND_EMAIL_RECEIPTS", True)
