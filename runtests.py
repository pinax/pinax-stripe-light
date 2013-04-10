import os
import sys

from django.conf import settings

settings.configure(
    DEBUG=True,
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
        }
    },
    # ROOT_URLCONF="payments.urls",
    INSTALLED_APPS=[
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sites",
        "jsonfield",
        "payments",
    ],
    STRIPE_PUBLIC_KEY="",
    STRIPE_SECRET_KEY="",
    PAYMENTS_PLANS={}
)

from django.test.simple import DjangoTestSuiteRunner

test_runner = DjangoTestSuiteRunner(verbosity=1)
failures = test_runner.run_tests(["payments"])

if failures:
    sys.exit(failures)
