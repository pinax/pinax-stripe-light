import decimal
import sys

from django.conf import settings

settings.configure(
    DEBUG=True,
    USE_TZ=True,
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
        }
    },
    ROOT_URLCONF="payments.urls",
    INSTALLED_APPS=[
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.sites",
        "django_forms_bootstrap",
        "jsonfield",
        "payments",
    ],
    SITE_ID=1,
    STRIPE_PUBLIC_KEY="",
    STRIPE_SECRET_KEY="",
    PAYMENTS_PLANS={
        "free": {
            "name": "Free Plan"
        },
        "entry": {
            "stripe_plan_id": "entry-monthly",
            "name": "Entry ($9.54/month)",
            "description": "The entry-level monthly subscription",
            "price": 9.54,
            "interval": "month",
            "currency": "usd"
        },
        "pro": {
            "stripe_plan_id": "pro-monthly",
            "name": "Pro ($19.99/month)",
            "description": "The pro-level monthly subscription",
            "price": 19.99,
            "interval": "month",
            "currency": "usd"
        },
        "premium": {
            "stripe_plan_id": "premium-monthly",
            "name": "Gold ($59.99/month)",
            "description": "The premium-level monthly subscription",
            "price": decimal.Decimal("59.99"),
            "interval": "month",
            "currency": "usd"
        }
    },
    SUBSCRIPTION_REQUIRED_EXCEPTION_URLS=["payments_subscribe"],
    SUBSCRIPTION_REQUIRED_REDIRECT="payments_subscribe",
    PAYMENTS_TRIAL_PERIOD_FOR_USER_CALLBACK="payments.tests.callbacks.callback_demo",
    PAYMENTS_PLAN_QUANTITY_CALLBACK="payments.tests.callbacks.quantity_call_back"
)

from django_nose import NoseTestSuiteRunner

test_runner = NoseTestSuiteRunner(verbosity=1)
failures = test_runner.run_tests(["payments"])

if failures:
    sys.exit(failures)
