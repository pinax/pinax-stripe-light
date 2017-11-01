import os

import django

DEBUG = True
USE_TZ = True
TIME_ZONE = "UTC"
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("PINAX_STRIPE_DATABASE_ENGINE", "django.db.backends.sqlite3"),
        "HOST": os.environ.get("PINAX_STRIPE_DATABASE_HOST", "127.0.0.1"),
        "NAME": os.environ.get("PINAX_STRIPE_DATABASE_NAME", "pinax_stripe"),
        "USER": os.environ.get("PINAX_STRIPE_DATABASE_USER", ""),
    }
}
MIDDLEWARE = [  # from 2.0 onwards, only MIDDLEWARE is used
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
if django.VERSION < (1, 10):
    MIDDLEWARE_CLASSES = MIDDLEWARE
ROOT_URLCONF = "pinax.stripe.tests.urls"
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "jsonfield",
    "pinax.stripe",
]
SITE_ID = 1
PINAX_STRIPE_PUBLIC_KEY = ""
PINAX_STRIPE_SECRET_KEY = "sk_test_01234567890123456789abcd"
PINAX_STRIPE_SUBSCRIPTION_REQUIRED_EXCEPTION_URLS = ["pinax_stripe_subscription_create"]
PINAX_STRIPE_SUBSCRIPTION_REQUIRED_REDIRECT = "pinax_stripe_subscription_create"
PINAX_STRIPE_HOOKSET = "pinax.stripe.tests.hooks.TestHookSet"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [
        "pinax/stripe/tests/templates"
    ],
    "APP_DIRS": True,
    "OPTIONS": {
        "debug": True,
        "context_processors": [
            "django.contrib.auth.context_processors.auth",
            "django.template.context_processors.debug",
            "django.template.context_processors.i18n",
            "django.template.context_processors.media",
            "django.template.context_processors.static",
            "django.template.context_processors.tz",
            "django.template.context_processors.request",
        ],
    },
}]
SECRET_KEY = "pinax-stripe-secret-key"
