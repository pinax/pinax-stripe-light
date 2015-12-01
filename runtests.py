#!/usr/bin/env python
import os
import sys

import django

from django.conf import settings

old = django.VERSION < (1, 8)

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
    PINAX_STRIPE_SUBSCRIPTION_REQUIRED_EXCEPTION_URLS=["pinax_stripe_subscription_create"],
    PINAX_STRIPE_SUBSCRIPTION_REQUIRED_REDIRECT="pinax_stripe_subscription_create",
    PINAX_STRIPE_HOOKSET="pinax.stripe.tests.hooks.TestHookSet",
    TEMPLATE_DIRS=[
        "pinax/stripe/tests/templates"
    ],
    TEMPLATES=[{
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            "pinax/stripe/tests/templates"
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": True,
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.{}.context_processors.debug".format("core" if old else "template"),
                "django.{}.context_processors.i18n".format("core" if old else "template"),
                "django.{}.context_processors.media".format("core" if old else "template"),
                "django.{}.context_processors.static".format("core" if old else "template"),
                "django.{}.context_processors.tz".format("core" if old else "template"),
                "django.{}.context_processors.request".format("core" if old else "template")
            ],
        },
    }]
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
