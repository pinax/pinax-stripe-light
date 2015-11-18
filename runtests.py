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
    ROOT_URLCONF="pinax.stripe.urls",
    INSTALLED_APPS=[
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.sites",
        "django_forms_bootstrap",
        "jsonfield",
        "pinax.stripe",
    ],
    SITE_ID=1,
    PINAX_STRIPE_PUBLIC_KEY="",
    PINAX_STRIPE_SECRET_KEY="",
    PINAX_STRIPE_PLANS={
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
    PINAX_STRIPE_SUBSCRIPTION_REQUIRED_EXCEPTION_URLS=["pinax_stripe_subscribe"],
    PINAX_STRIPE_SUBSCRIPTION_REQUIRED_REDIRECT="pinax_stripe_subscribe",
    PINAX_STRIPE_HOOKSET="pinax.stripe.tests.hooks.TestHookSet"
)


def runtests(*test_args):
    if not settings.configured:
        settings.configure(**DEFAULT_SETTINGS)

    django.setup()

    parent = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, parent)

    try:
        from django.test.runner import DiscoverRunner
        runner_class = DiscoverRunner
        if not test_args:
            test_args = ["pinax.stripe.tests"]
    except ImportError:
        from django.test.simple import DjangoTestSuiteRunner
        runner_class = DjangoTestSuiteRunner
        test_args = ["tests"]

    failures = runner_class(verbosity=1, interactive=True, failfast=False).run_tests(test_args)
    sys.exit(failures)


if __name__ == "__main__":
    runtests(*sys.argv[1:])
