#!/usr/bin/env python
import decimal
import os
import sys

import django

from django.conf import settings


DEFAULT_SETTINGS = dict(
    DEBUG=True,
    USE_TZ=True,
    TIME_ZONE='UTC',
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
        }
    },
    MIDDLEWARE_CLASSES=[
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware"
    ],
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


def runtests(*test_args):
    if not settings.configured:
        settings.configure(**DEFAULT_SETTINGS)

    # Compatibility with Django 1.7's stricter initialization
    if hasattr(django, "setup"):
        django.setup()

    parent = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, parent)

    try:
        from django.test.runner import DiscoverRunner
        runner_class = DiscoverRunner
        test_args = ["payments.tests"]
    except ImportError:
        from django.test.simple import DjangoTestSuiteRunner
        runner_class = DjangoTestSuiteRunner
        test_args = ["tests"]

    failures = runner_class(
        verbosity=1, interactive=True, failfast=False).run_tests(test_args)
    sys.exit(failures)


if __name__ == "__main__":
    runtests(*sys.argv[1:])
